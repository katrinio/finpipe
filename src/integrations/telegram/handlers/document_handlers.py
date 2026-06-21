import logging
import tempfile
from pathlib import Path

from src.infrastructure.security.exceptions import SignatureDecryptionError
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.document_menu import (
    build_bank_day_reply_prompt_menu,
    build_bank_day_start_menu,
    build_document_menu,
    build_invoice_menu,
    build_invoice_send_prompt_menu,
)
from src.integrations.telegram.ui.messages import BankMessages, InvoiceMessages, MsgIcon
from src.services.bank.bank_confirmation import generate_bank_confirmation_pdf
from src.services.bank.bank_extract import extract_amount
from src.services.bank.exceptions import BankPdfError
from src.services.conversion_order.exceptions import TransferRequestError
from src.services.invoice.exceptions import InvoiceError
from src.services.monitoring.event_logger import EventLogger
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm import UserConfig
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.storage.orm.system.processed_message import ProcessedMessage
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.storage.orm.user.pending_bank_reply import PendingBankReply
from src.storage.orm.user.signature import Signature
from src.utils.credentials import EnvVar
from src.utils.files import delete_file
from src.utils.utils import Utils
from src.workflows.run_bank_request import BankDocuments, fetch_bank_email_workflow, send_bank_email_reply
from src.workflows.run_invoice_delivery import discard_invoice_pdf, generate_and_send_invoice, send_invoice_email
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf
from src.workflows.tasks.generate_invoice import generate_invoice_pdf

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
        readiness_error = self._invoice_readiness_error(telegram_id)
        if readiness_error is not None:
            self.telegram.send_message(telegram_id, readiness_error, reply_markup=build_invoice_menu())
            return
        self.telegram.send_message(telegram_id, InvoiceMessages.Generation.IN_PROGRESS)
        try:
            generate_and_send_invoice(telegram_id)
        except InvoiceError as error:
            LOGGER.warning("Salary invoice generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_invoice_menu())
            return
        LOGGER.info("Salary invoice generated for Telegram user %s", telegram_id)
        to_email = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", "")
        self.telegram.send_message(
            telegram_id, InvoiceMessages.Generation.SEND_PROMPT.format(to_email), reply_markup=build_invoice_send_prompt_menu()
        )

    def invoice_send_to_company(self, telegram_id: int) -> None:
        LOGGER.info("Invoice send to company requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessages.Generation.SENDING)
        try:
            send_invoice_email(telegram_id)
        except InvoiceError as error:
            LOGGER.warning("Invoice email sending failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_invoice_menu())
            return
        LOGGER.info("Invoice email sent for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessages.Generation.SENT_TO_COMPANY, reply_markup=build_invoice_menu())

    def invoice_skip_send(self, telegram_id: int) -> None:
        discard_invoice_pdf()
        self.telegram.send_message(telegram_id, InvoiceMessages.Generation.SENT, reply_markup=build_invoice_menu())

    def get_invoice_amount(self, telegram_id: int) -> None:
        current_amount = UserConfig.get_by_owner(telegram_id)
        if current_amount is None or current_amount.invoice_amount_eur is None:
            self.telegram.send_message(telegram_id, InvoiceMessages.Validation.NO_INVOICE_AMOUNT, reply_markup=build_invoice_menu())
            return

        self.telegram.send_message(
            telegram_id,
            f"💶 Текущая сумма инвойса: {current_amount.invoice_amount_eur} EUR",
            reply_markup=build_invoice_menu(),
        )

    def bank_day_info(self, telegram_id: int) -> None:
        status = SystemStatusService.get_status(telegram_id)
        lines = [
            f"{MsgIcon.status(status.company and status.bank_details)} Профиль (компания + реквизиты)",
            f"{MsgIcon.status(status.signature)} Подпись",
            f"{MsgIcon.status(status.gmail)} Gmail",
        ]
        text = BankMessages.BankDay.INFO.format(status_lines="\n".join(lines))
        self.telegram.send_message(telegram_id, text, reply_markup=build_bank_day_start_menu())

    def handle_skip(self, telegram_id: int) -> None:
        """Обрабатывает «✖️ Не отправлять» — банковский ответ или инвойс."""
        if PendingBankReply.get(telegram_id) is not None:
            self.bank_day_skip_reply(telegram_id)
        else:
            self.invoice_skip_send(telegram_id)

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

    def bank_day(self, telegram_id: int) -> None:
        """Банковский день: письмо банка → подтверждение + запрос на конвертацию → все три документа."""

        LOGGER.info("Bank day workflow started for Telegram user %s", telegram_id)

        readiness_error = self._bank_confirmation_readiness_error(telegram_id)
        if readiness_error is not None:
            self.telegram.send_message(telegram_id, readiness_error, reply_markup=build_document_menu())
            return

        self.telegram.send_message(telegram_id, BankMessages.BankDay.IN_PROGRESS)

        # Шаг 1: получить оригинальный PDF из письма банка
        try:
            fetch_result = fetch_bank_email_workflow(telegram_id=telegram_id)
        except RuntimeError as error:
            LOGGER.warning("Bank day: Gmail not configured for Telegram user %s: %s", telegram_id, error)
            self.telegram.send_message(telegram_id, BankMessages.Validation.BANK_EMAIL_NOT_CONFIGURED, reply_markup=build_document_menu())
            return

        if fetch_result is None:
            self.telegram.send_message(telegram_id, BankMessages.Search.NOT_FOUND, reply_markup=build_document_menu())
            return

        bank_pdf_path, bank_email = fetch_result

        bank_confirmation_path: Path | None = None
        conversion_order_path: Path | None = None
        invoice_pdf_path: Path | None = None
        amount: float = 0.0

        try:
            # Шаг 2: извлечь сумму и сохранить в конфиге пользователя
            amount = extract_amount(bank_pdf_path)
            UserConfig.upsert(telegram_id=telegram_id, bank_received_amount_eur=amount)
            LOGGER.info("Bank day: extracted amount %.2f EUR for Telegram user %s", amount, telegram_id)
            self.telegram.send_message(telegram_id, BankMessages.BankDay.EMAIL_RECEIVED.format(f"{amount:.2f}"))

            # Шаг 3: заполнить Bank Confirmation
            bank_confirmation_path = self._fill_bank_confirmation_pdf(telegram_id, bank_pdf_path, amount)
            self.telegram.send_message(telegram_id, BankMessages.BankDay.CONFIRMATION_READY)

            # Шаг 4: сгенерировать Conversion Order на ту же сумму
            conversion_order_path = generate_conversion_order_pdf(
                telegram_id=telegram_id,
                invoice_amount_eur=None,
                bank_received_amount_eur=amount,
                conversion_amount_eur=amount,
            )
            self.telegram.send_message(telegram_id, BankMessages.BankDay.CONVERSION_READY)

            # Шаг 5: сгенерировать инвойс за 20-е предыдущего месяца (для ответного письма)
            prev_month_20 = Utils.today().replace(day=20)
            if prev_month_20.month == 1:
                prev_month_20 = prev_month_20.replace(year=prev_month_20.year - 1, month=12)
            else:
                prev_month_20 = prev_month_20.replace(month=prev_month_20.month - 1)
            invoice_pdf_path = generate_invoice_pdf(telegram_id=telegram_id, invoice_date=prev_month_20)
            self.telegram.send_message(telegram_id, BankMessages.BankDay.INVOICE_READY)

            # Шаг 6: отправить три документа в Telegram
            self.telegram.send_document(telegram_id, bank_confirmation_path)
            self.telegram.send_document(telegram_id, conversion_order_path)
            self.telegram.send_document(telegram_id, invoice_pdf_path)

        except (BankPdfError, FileNotFoundError, ValueError, TransferRequestError, InvoiceError) as error:
            LOGGER.warning("Bank day workflow failed for Telegram user %s: %s", telegram_id, error)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_document_menu())
            delete_file(bank_pdf_path, LOGGER)
            if bank_confirmation_path is not None:
                delete_file(bank_confirmation_path, LOGGER)
            if conversion_order_path is not None:
                delete_file(conversion_order_path, LOGGER)
                delete_file(conversion_order_path.with_suffix(".docx"), LOGGER)
            if invoice_pdf_path is not None:
                delete_file(invoice_pdf_path, LOGGER)
                delete_file(invoice_pdf_path.with_suffix(".docx"), LOGGER)
            return
        finally:
            # Оригинальный PDF банка больше не нужен после Telegram-отправки
            delete_file(bank_pdf_path, LOGGER)

        # Шаг 7: сохранить состояние для отложенного ответа банку
        PendingBankReply.save(
            telegram_id=telegram_id,
            thread_id=bank_email.thread_id,
            subject=bank_email.subject,
            sender=bank_email.sender,
            cc=bank_email.cc,
            message_id=bank_email.message_id,
            invoice_pdf_path=str(invoice_pdf_path),
            bank_confirmation_path=str(bank_confirmation_path),
            conversion_order_path=str(conversion_order_path),
        )

        LOGGER.info("Bank day workflow completed for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.BankDay.DONE.format(f"{amount:.2f}"))
        to_email = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", "")
        self.telegram.send_message(telegram_id, BankMessages.BankDay.REPLY_PROMPT.format(to_email), reply_markup=build_bank_day_reply_prompt_menu())

    def bank_day_reply_to_bank(self, telegram_id: int) -> None:
        LOGGER.info("Bank day reply to bank requested by Telegram user %s", telegram_id)

        pending = PendingBankReply.get(telegram_id)
        if pending is None:
            LOGGER.warning("No pending bank reply for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BankMessages.BankDay.REPLY_NO_PENDING, reply_markup=build_document_menu())
            return

        self.telegram.send_message(telegram_id, BankMessages.BankDay.REPLY_SENDING)
        try:
            from src.integrations.gmail.gmail_models import BankEmail

            bank_email = BankEmail(
                subject=pending.subject,
                sender=pending.sender,
                date="",
                message_id=pending.message_id,
                thread_id=pending.thread_id,
                cc=pending.cc,
            )
            docs = BankDocuments(
                invoice_pdf=Path(pending.invoice_pdf_path),
                bank_confirmation=Path(pending.bank_confirmation_path),
                conversion_order=Path(pending.conversion_order_path),
            )
            send_bank_email_reply(telegram_id=telegram_id, bank_email=bank_email, docs=docs)
        except Exception as error:
            LOGGER.warning("Bank day reply failed for Telegram user %s: %s", telegram_id, error)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_document_menu())
            return
        finally:
            if pending is not None:
                delete_file(Path(pending.invoice_pdf_path), LOGGER)
                delete_file(Path(pending.bank_confirmation_path), LOGGER)
                delete_file(Path(pending.conversion_order_path), LOGGER)
                delete_file(Path(pending.conversion_order_path).with_suffix(".docx"), LOGGER)
                PendingBankReply.clear(telegram_id)

        LOGGER.info("Bank day reply sent for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.BankDay.REPLY_SENT, reply_markup=build_document_menu())

    def bank_day_skip_reply(self, telegram_id: int) -> None:
        pending = PendingBankReply.get(telegram_id)
        if pending is not None:
            delete_file(Path(pending.invoice_pdf_path), LOGGER)
            delete_file(Path(pending.bank_confirmation_path), LOGGER)
            delete_file(Path(pending.conversion_order_path), LOGGER)
            delete_file(Path(pending.conversion_order_path).with_suffix(".docx"), LOGGER)
            ProcessedMessage.unmark_bank_day_processed(pending.message_id)
            PendingBankReply.clear(telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.BankDay.REPLY_SKIPPED, reply_markup=build_document_menu())

    def _invoice_readiness_error(self, telegram_id: int) -> str | None:
        status = SystemStatusService.get_status(telegram_id)
        if not status.company or not status.bank_details:
            return InvoiceMessages.Validation.PROFILE_REQUIRED
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.invoice_amount_eur is None:
            return InvoiceMessages.Validation.NO_INVOICE_AMOUNT
        return None

    def _bank_confirmation_readiness_error(self, telegram_id: int) -> str | None:
        status = SystemStatusService.get_status(telegram_id)
        if not status.gmail:
            return BankMessages.Validation.GMAIL_NOT_CONNECTED
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
