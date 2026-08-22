import logging
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.document_menu import (
    build_document_menu,
    build_invoice_menu,
)
from src.integrations.telegram.ui.messages import BankMessages, InvoiceMessages
from src.services.bank.exceptions import BankPdfError
from src.services.conversion_order.exceptions import TransferRequestError
from src.services.invoice.exceptions import InvoiceError
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm import Signature, UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.workflows.run_bank_confirmation_delivery import generate_and_send_bank_confirmation
from src.workflows.run_conversion_request_delivery import generate_and_send_conversion_request
from src.workflows.run_invoice_delivery import generate_and_send_invoice

LOGGER = logging.getLogger(__name__)


class DocumentHandlers:
    """Запускает документные workflow из Telegram-команд."""

    MAX_BANK_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024

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

    def start_bank_document_upload(self, telegram_id: int) -> None:
        """Переводит пользователя в режим загрузки исходного банковского PDF."""

        readiness_error = self._signed_document_readiness_error(telegram_id)
        if readiness_error is not None:
            self.telegram.send_message(telegram_id, readiness_error, reply_markup=build_document_menu())
            return

        UserStateService.set_state(telegram_id, UserState.WAITING_BANK_DOCUMENT_UPLOAD)
        self.telegram.send_message(telegram_id, BankMessages.Confirmation.UPLOAD, reply_markup=build_document_menu())

    def handle_bank_document_upload(
        self,
        telegram_id: int,
        file_name: str,
        file_size: int,
        file_bytes: bytes,
    ) -> None:
        """Проверяет банковский PDF, формирует подтверждение и отправляет его в Telegram."""

        validation_error = self._validate_bank_document(file_name, file_size, file_bytes)
        if validation_error is not None:
            self.telegram.send_message(telegram_id, validation_error, reply_markup=build_document_menu())
            return

        self.telegram.send_message(telegram_id, BankMessages.Confirmation.IN_PROGRESS)
        try:
            generate_and_send_bank_confirmation(self.telegram, telegram_id, file_bytes)
        except BankPdfError, FileNotFoundError, ValueError:
            LOGGER.warning("Bank confirmation generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BankMessages.Validation.GENERATION_FAILED, reply_markup=build_document_menu())
            return

        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, BankMessages.Confirmation.SENT, reply_markup=build_document_menu())

    def conversion_request(self, telegram_id: int) -> None:
        """Генерирует Conversion Request на сумму последнего банковского документа."""

        readiness_error = self._signed_document_readiness_error(telegram_id)
        if readiness_error is not None:
            self.telegram.send_message(telegram_id, readiness_error, reply_markup=build_document_menu())
            return

        user_config = UserConfig.get_by_owner(telegram_id)
        amount = user_config.bank_received_amount_eur if user_config is not None else None
        if amount is None:
            self.telegram.send_message(telegram_id, BankMessages.Validation.NO_BANK_AMOUNT, reply_markup=build_document_menu())
            return

        self.telegram.send_message(telegram_id, BankMessages.ConversionRequest.IN_PROGRESS)
        try:
            generate_and_send_conversion_request(self.telegram, telegram_id, amount)
        except TransferRequestError, FileNotFoundError, ValueError:
            LOGGER.warning("Conversion request generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BankMessages.Validation.GENERATION_FAILED, reply_markup=build_document_menu())
            return

        self.telegram.send_message(telegram_id, BankMessages.ConversionRequest.SENT, reply_markup=build_document_menu())

    def _invoice_readiness_error(self, telegram_id: int) -> str | None:
        status = SystemStatusService.get_status(telegram_id)
        if not status.company or not status.bank_details:
            return InvoiceMessages.Validation.PROFILE_REQUIRED
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.invoice_amount_eur is None:
            return InvoiceMessages.Validation.NO_INVOICE_AMOUNT
        return None

    @staticmethod
    def _signed_document_readiness_error(telegram_id: int) -> str | None:
        if CompanyProfile.get_by_owner(telegram_id) is None or BankDetails.get_by_owner(telegram_id) is None:
            return BankMessages.Validation.PROFILE_REQUIRED
        if not Signature.is_usable(telegram_id):
            return BankMessages.Validation.SIGNATURE_REQUIRED
        return None

    @classmethod
    def _validate_bank_document(cls, file_name: str, file_size: int, file_bytes: bytes) -> str | None:
        if not file_name.lower().endswith(".pdf"):
            return BankMessages.Validation.NOT_PDF
        if file_size > cls.MAX_BANK_DOCUMENT_SIZE_BYTES:
            return BankMessages.Validation.TOO_LARGE
        if not file_bytes.startswith(b"%PDF-"):
            return BankMessages.Validation.INVALID_PDF
        try:
            PdfReader(BytesIO(file_bytes))
        except PdfReadError, OSError, ValueError:
            return BankMessages.Validation.INVALID_PDF
        return None
