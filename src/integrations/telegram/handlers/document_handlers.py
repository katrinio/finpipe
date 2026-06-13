import logging

from src.constants import Message
from src.infrastructure.security.exceptions import SignatureDecryptionError
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.document_menu import build_document_menu, build_invoice_menu
from src.integrations.telegram.ui.messages import BankMessagesV2, ConversionOrderMessages, InvoiceMessagesV2
from src.services.bank.exceptions import BankPdfError
from src.services.conversion_order.exceptions import TransferRequestError
from src.services.invoice.exceptions import InvoiceError
from src.storage.orm import UserConfig
from src.workflows.run_invoice_delivery import generate_and_send_invoice
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf

LOGGER = logging.getLogger(__name__)


class DocumentHandlers:
    """Запускает документные workflow из Telegram-команд."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def start_invoice_amount_input(self, telegram_id: int) -> None:
        """Переводит пользователя в режим ввода суммы Salary Invoice."""

        UserStateService.set_state(telegram_id, UserState.WAITING_INVOICE_AMOUNT)
        self.telegram.send_message(telegram_id, InvoiceMessagesV2.Amount.INPUT, reply_markup=build_invoice_menu())

    def handle_invoice_amount_input(self, telegram_id: int, text: str | None) -> None:
        """Сохраняет сумму Salary Invoice после валидации текстового ввода."""

        if text is None or not text.isdigit() or int(text) <= 0:
            self.telegram.send_message(telegram_id, InvoiceMessagesV2.Validation.NOT_INT, reply_markup=build_invoice_menu())
            return

        amount = int(text)
        UserConfig.upsert(telegram_id=telegram_id, invoice_amount_eur=amount)
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessagesV2.Amount.SAVED.format(amount), reply_markup=build_invoice_menu())

    def invoice(self, telegram_id: int) -> None:
        """Запускает генерацию Salary Invoice и отправляет результат пользователю."""

        LOGGER.info("Salary invoice generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessagesV2.Generation.IN_PROGRESS)
        try:
            generate_and_send_invoice(telegram_id)
        except InvoiceError as error:
            LOGGER.warning("Salary invoice generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_invoice_menu())
            return
        LOGGER.info("Salary invoice generated for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, InvoiceMessagesV2.Generation.SENT, reply_markup=build_invoice_menu())

    def get_invoice_amount(self, telegram_id: int) -> None:
        """Показывает текущую сумму Salary Invoice из пользовательских настроек."""

        current_amount = UserConfig.get_by_owner(telegram_id)
        if current_amount is None or current_amount.invoice_amount_eur is None:
            self.telegram.send_message(telegram_id, InvoiceMessagesV2.Validation.NO_INVOICE_AMOUNT, reply_markup=build_invoice_menu())
            return

        self.telegram.send_message(
            telegram_id,
            f"💶 Текущая сумма Salary Invoice: {current_amount.invoice_amount_eur} EUR",
            reply_markup=build_invoice_menu(),
        )

    def bank_confirmation(self, telegram_id: int) -> None:
        """Генерирует подтверждение для банка и отправляет его пользователю."""

        LOGGER.info("Bank confirmation generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BankMessagesV2.Generation.IN_PROGRESS)

        try:
            bank_confirmation_path = generate_bank_confirmation(telegram_id)
        except FileNotFoundError, SignatureDecryptionError:
            LOGGER.info("Bank confirmation failed due to missing signature for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BankMessagesV2.Validation.SIGNATURE_REQUIRED, reply_markup=build_document_menu())
            return
        except BankPdfError as error:
            LOGGER.info("Bank confirmation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_document_menu())
            return
        LOGGER.info("Bank confirmation generated for Telegram user %s", telegram_id)
        self.telegram.send_document(telegram_id, bank_confirmation_path)
        self.telegram.send_message(telegram_id, BankMessagesV2.Generation.SENT, reply_markup=build_document_menu())

    def conversion_order(self, telegram_id: int) -> None:
        """Генерирует Conversion Order для текущего пользователя."""

        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.exchange_amount_eur is None:
            LOGGER.warning("Conversion order generation blocked by missing exchange amount for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, ConversionOrderMessages.NO_EXCHANGE_AMOUNT, reply_markup=build_document_menu())
            return

        try:
            LOGGER.info("Conversion order generation requested by Telegram user %s", telegram_id)
            conversion_order_pdf_path = generate_conversion_order_pdf(
                telegram_id=telegram_id,
                invoice_amount_eur=config.invoice_amount_eur,
                received_amount_eur=config.received_amount_eur,
                exchange_amount_eur=config.exchange_amount_eur,
            )
        except TransferRequestError as error:
            LOGGER.warning("Conversion order generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error), reply_markup=build_document_menu())
            return
        LOGGER.info("Conversion order generated for Telegram user %s", telegram_id)
        self.telegram.send_document(telegram_id, conversion_order_pdf_path)
        self.telegram.send_message(telegram_id, Message.CONVERSION_ORDER_GENERATED, reply_markup=build_document_menu())
