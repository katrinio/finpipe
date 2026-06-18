import logging
import tempfile
from pathlib import Path

from src.constants import Message
from src.infrastructure.security.exceptions import SignatureDecryptionError
from src.integrations.gmail.auth import get_gmail_service
from src.integrations.gmail.search import find_bank_email
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.document_menu import (
    build_bank_confirmation_menu,
    build_conversion_order_menu,
    build_document_menu,
    build_invoice_menu,
)
from src.integrations.telegram.ui.messages import BankMessages, ConversionOrderMessages, InvoiceMessages
from src.services.bank.bank_confirmation import generate_bank_confirmation_pdf
from src.services.bank.bank_extract import extract_amount
from src.services.bank.exceptions import BankPdfError
from src.services.conversion_order.exceptions import TransferRequestError
from src.services.invoice.exceptions import InvoiceError
from src.services.monitoring.event_logger import EventLogger
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm import UserConfig
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.storage.orm.user.signature import Signature
from src.utils.files import delete_file
from src.utils.utils import Utils
from src.workflows.run_bank_request import fetch_bank_email_workflow
from src.workflows.run_invoice_delivery import generate_and_send_invoice
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf

LOGGER = logging.getLogger(__name__)


class DocumentHandlers:
    """Запускает документные workflow из Telegram-команд."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def start_invoice_amount_input(self, telegram_id: int) -> None:
        UserStateService.set_state(telegram_id, UserState.WAITING_INVOICE_AMOUNT)
        self.telegram.send_message(telegram_id, InvoiceMessages.Amount.INPUT, reply_markup=build_invoice_menu())

    def handle_invoice_amount_input(self, telegram_id: int, text: str | None) -> None:
        if text is None or not text.isdigit() or int(text) <= 0:
            self.telegram.send_message(telegram_id, InvoiceMessages.Validation.NOT_INT, reply_markup=build_invoice_menu())
            return

        amount = int(text)
        UserConfig.upsert(telegram_id=telegram_id, invoice_amount_eur=amount)
        EventLogger.log(
            EventType.SETTINGS_UPDATED,
            EventSeverity.INFO,
            {"telegram_id": telegram_id, "section": "user_config"},
        )
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessages.Amount.SAVED.format(amount), reply_markup=build_invoice_menu())

    def invoice(self, telegram_id: int) -> None:
        LOGGER.info("Salary invoice generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessages.Generation.IN_PROGRESS)
        try:
            generate_and_send_invoice(telegram_id)
        except InvoiceError as error:
            LOGGER.warning("Salary invoice generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_invoice_menu())
            return
        LOGGER.info("Salary invoice generated for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessages.Generation.SENT, reply_markup=build_invoice_menu())

    def get_invoice_amount(self, telegram_id: int) -> None:
        current_amount = UserConfig.get_by_owner(telegram_id)
        if current_amount is None or current_amount.invoice_amount_eur is None:
            self.telegram.send_message(telegram_id, InvoiceMessages.Validation.NO_INVOICE_AMOUNT, reply_markup=build_invoice_menu())
            return

        self.telegram.send_message(
            telegram_id,
            f"💶 Текущая сумма Salary Invoice: {current_amount.invoice_amount_eur} EUR",
            reply_markup=build_invoice_menu(),
        )

    def bank_confirmation(self, telegram_id: int) -> None:
        LOGGER.info("Bank confirmation generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.Generation.IN_PROGRESS)

        try:
            bank_confirmation_path = generate_bank_confirmation(telegram_id)
        except FileNotFoundError, SignatureDecryptionError:
            LOGGER.info("Bank confirmation failed due to missing signature for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BankMessages.Validation.SIGNATURE_REQUIRED, reply_markup=build_document_menu())
            return
        except BankPdfError as error:
            LOGGER.info("Bank confirmation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_document_menu())
            return

        LOGGER.info("Bank confirmation generated for Telegram user %s", telegram_id)
        try:
            self.telegram.send_document(telegram_id, bank_confirmation_path)
        finally:
            delete_file(bank_confirmation_path, LOGGER)
        self.telegram.send_message(telegram_id, BankMessages.Generation.SENT, reply_markup=build_document_menu())

    def start_bank_confirmation_upload(self, telegram_id: int) -> None:
        LOGGER.info("Bank confirmation upload requested by Telegram user %s", telegram_id)
        UserStateService.set_state(telegram_id, UserState.WAITING_BANK_CONFIRMATION_UPLOAD)
        self.telegram.send_message(telegram_id, BankMessages.Menu.UPLOAD, reply_markup=build_bank_confirmation_menu())

    def handle_bank_confirmation_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        LOGGER.info("Bank confirmation manual upload started for Telegram user %s", telegram_id)
        if not file_name.lower().endswith(".pdf"):
            self.telegram.send_message(telegram_id, BankMessages.Validation.NOT_PDF, reply_markup=build_bank_confirmation_menu())
            return

        readiness_error = self._bank_confirmation_readiness_error(telegram_id)
        if readiness_error is not None:
            self.telegram.send_message(telegram_id, readiness_error, reply_markup=build_bank_confirmation_menu())
            return

        source_path = self._write_temp_pdf(file_name, file_bytes)
        output_path: Path | None = None
        try:
            amount = extract_amount(source_path)
            output_path = self._fill_bank_confirmation_pdf(telegram_id, source_path, amount)
        except (BankPdfError, FileNotFoundError, ValueError) as error:
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_bank_confirmation_menu())
            return
        finally:
            delete_file(source_path, LOGGER)

        try:
            assert output_path is not None
            self.telegram.send_document(telegram_id, output_path)
        finally:
            if output_path is not None:
                delete_file(output_path, LOGGER)

        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.Generation.FILLED, reply_markup=build_bank_confirmation_menu())

    def check_bank_email(self, telegram_id: int) -> None:
        LOGGER.info("Bank email check requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.Search.CHECKING, reply_markup=build_bank_confirmation_menu())

        try:
            bank_email = find_bank_email(get_gmail_service(), owner_telegram_id=telegram_id)
        except RuntimeError as error:
            LOGGER.warning("Bank email search config is missing for Telegram user %s: %s", telegram_id, error)
            self.telegram.send_message(telegram_id, BankMessages.Validation.BANK_EMAIL_NOT_CONFIGURED, reply_markup=build_bank_confirmation_menu())
            return

        if bank_email is None:
            self.telegram.send_message(telegram_id, BankMessages.Search.NOT_FOUND, reply_markup=build_bank_confirmation_menu())
            return

        self.telegram.send_message(
            telegram_id,
            f"{BankMessages.Search.FOUND}\nSubject: {bank_email.subject}\nFrom: {bank_email.sender}\nDate: {bank_email.date}",
            reply_markup=build_bank_confirmation_menu(),
        )

    def get_and_process_bank_email(self, telegram_id: int) -> None:
        LOGGER.info("Bank email processing requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.Generation.IN_PROGRESS, reply_markup=build_bank_confirmation_menu())

        readiness_error = self._bank_confirmation_readiness_error(telegram_id)
        if readiness_error is not None:
            self.telegram.send_message(telegram_id, readiness_error, reply_markup=build_bank_confirmation_menu())
            return

        try:
            bank_template_path = fetch_bank_email_workflow(owner_telegram_id=telegram_id)
        except RuntimeError as error:
            LOGGER.warning("Bank email processing stopped due to missing settings for Telegram user %s: %s", telegram_id, error)
            self.telegram.send_message(telegram_id, BankMessages.Validation.BANK_EMAIL_NOT_CONFIGURED, reply_markup=build_bank_confirmation_menu())
            return

        if bank_template_path is None:
            self.telegram.send_message(telegram_id, BankMessages.Search.NOT_FOUND, reply_markup=build_bank_confirmation_menu())
            return

        output_path: Path | None = None
        try:
            amount = extract_amount(bank_template_path)
            output_path = self._fill_bank_confirmation_pdf(telegram_id, bank_template_path, amount)
            self.telegram.send_document(telegram_id, bank_template_path)
            self.telegram.send_document(telegram_id, output_path)
        except (BankPdfError, FileNotFoundError, ValueError) as error:
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_bank_confirmation_menu())
            return
        finally:
            delete_file(bank_template_path, LOGGER)
            if output_path is not None:
                delete_file(output_path, LOGGER)

        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.Generation.ORIGINAL_AND_FILLED, reply_markup=build_bank_confirmation_menu())

    def conversion_order_menu(self, telegram_id: int) -> None:
        config = UserConfig.get_by_owner(telegram_id)
        amount = config.conversion_amount_eur if config is not None else None
        message = ConversionOrderMessages.Amount.CURRENT.format(amount) if amount is not None else ConversionOrderMessages.Amount.NOT_SET
        self.telegram.send_message(telegram_id, message, reply_markup=build_conversion_order_menu())

    def start_conversion_amount_input(self, telegram_id: int) -> None:
        UserStateService.set_state(telegram_id, UserState.WAITING_CONVERSION_AMOUNT)
        self.telegram.send_message(telegram_id, ConversionOrderMessages.Amount.INPUT, reply_markup=build_conversion_order_menu())

    def handle_conversion_amount_input(self, telegram_id: int, text: str | None) -> None:
        if text is None:
            self.telegram.send_message(telegram_id, ConversionOrderMessages.Validation.NOT_INT, reply_markup=build_conversion_order_menu())
            return

        try:
            amount = float(text)
        except ValueError:
            self.telegram.send_message(telegram_id, ConversionOrderMessages.Validation.NOT_INT, reply_markup=build_conversion_order_menu())
            return

        if amount <= 0:
            self.telegram.send_message(telegram_id, ConversionOrderMessages.Validation.NOT_INT, reply_markup=build_conversion_order_menu())
            return

        UserConfig.upsert(telegram_id=telegram_id, conversion_amount_eur=amount)
        EventLogger.log(
            EventType.SETTINGS_UPDATED,
            EventSeverity.INFO,
            {"telegram_id": telegram_id, "section": "user_config"},
        )
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, ConversionOrderMessages.Amount.SAVED.format(amount), reply_markup=build_conversion_order_menu())

    def use_bank_amount(self, telegram_id: int) -> None:
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.bank_received_amount_eur is None:
            self.telegram.send_message(telegram_id, ConversionOrderMessages.Validation.NO_BANK_AMOUNT, reply_markup=build_conversion_order_menu())
            return

        UserConfig.upsert(telegram_id=telegram_id, conversion_amount_eur=config.bank_received_amount_eur)
        EventLogger.log(
            EventType.SETTINGS_UPDATED,
            EventSeverity.INFO,
            {"telegram_id": telegram_id, "section": "user_config"},
        )
        self.telegram.send_message(
            telegram_id,
            ConversionOrderMessages.Amount.FROM_BANK_SAVED.format(config.bank_received_amount_eur),
            reply_markup=build_conversion_order_menu(),
        )

    def _bank_confirmation_readiness_error(self, telegram_id: int) -> str | None:
        status = SystemStatusService.get_status(telegram_id)
        if not status.company or not status.bank_details:
            return BankMessages.Validation.PROFILE_REQUIRED
        if not Signature.is_usable(telegram_id):
            return BankMessages.Validation.SIGNATURE_REQUIRED
        return None

    def _fill_bank_confirmation_pdf(self, telegram_id: int, input_pdf: Path, amount: float) -> Path:
        company_profile = CompanyProfile.get_by_owner(telegram_id)
        bank_details = BankDetails.get_by_owner(telegram_id)
        signature = Signature.resolve_workflow_signature_path(telegram_id)
        if company_profile is None or bank_details is None:
            msg = BankMessages.Validation.PROFILE_REQUIRED
            raise ValueError(msg)
        if signature is None:
            msg = BankMessages.Validation.SIGNATURE_REQUIRED
            raise FileNotFoundError(msg)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"bank-confirmation-{telegram_id}-") as output_file:
            output_pdf = Path(output_file.name)
        generate_bank_confirmation_pdf(
            input_pdf=input_pdf,
            output_pdf=output_pdf,
            amount=amount,
            date=Utils.today().isoformat(),
            company_profile=company_profile,
            bank_details=bank_details,
            signature=signature,
        )
        return output_pdf

    @staticmethod
    def _write_temp_pdf(file_name: str, file_bytes: bytes) -> Path:
        suffix = Path(file_name).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()
            return Path(temp_file.name)

    def conversion_order(self, telegram_id: int) -> None:
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.conversion_amount_eur is None:
            LOGGER.warning("Conversion order generation blocked by missing conversion amount for Telegram user %s", telegram_id)
            self.telegram.send_message(
                telegram_id, ConversionOrderMessages.Validation.NO_CONVERSION_AMOUNT, reply_markup=build_conversion_order_menu()
            )
            return

        try:
            LOGGER.info("Conversion order generation requested by Telegram user %s", telegram_id)
            conversion_order_pdf_path = generate_conversion_order_pdf(
                telegram_id=telegram_id,
                invoice_amount_eur=config.invoice_amount_eur,
                bank_received_amount_eur=config.bank_received_amount_eur,
                conversion_amount_eur=config.conversion_amount_eur,
            )
        except TransferRequestError as error:
            LOGGER.warning("Conversion order generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_conversion_order_menu())
            return

        LOGGER.info("Conversion order generated for Telegram user %s", telegram_id)
        try:
            self.telegram.send_document(telegram_id, conversion_order_pdf_path)
        finally:
            delete_file(conversion_order_pdf_path, LOGGER)
            delete_file(conversion_order_pdf_path.with_suffix(".docx"), LOGGER)
        self.telegram.send_message(telegram_id, Message.CONVERSION_ORDER_GENERATED, reply_markup=build_conversion_order_menu())
