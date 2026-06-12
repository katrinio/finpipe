import logging

from src.constants import Message
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.messages import BotInfo
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
        self.telegram.send_message(telegram_id, "💰 Введите сумму Salary Invoice:")

    def handle_invoice_amount_input(self, telegram_id: int, text: str | None) -> None:
        """Сохраняет сумму Salary Invoice после валидации текстового ввода."""

        if text is None or not text.isdigit() or int(text) <= 0:
            self.telegram.send_message(
                telegram_id,
                "❌ Сумма должна содержать только цифры.\nПример: 1500",
            )
            return

        amount = int(text)
        UserConfig.upsert(telegram_id=telegram_id, invoice_amount=amount)
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, f"✅ Сумма Salary Invoice сохранена: {amount} EUR")

    def invoice(self, telegram_id: int) -> None:
        """Запускает генерацию Salary Invoice и отправляет результат пользователю."""

        LOGGER.info("Salary invoice generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.GENERATING_INVOICE)
        try:
            generate_and_send_invoice(telegram_id)
        except ValueError as error:
            LOGGER.warning("Salary invoice generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error))
            return
        LOGGER.info("Salary invoice generated for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.INVOICE_SENT)

    def get_invoice_amount(self, telegram_id: int) -> None:
        """Показывает текущую сумму Salary Invoice из пользовательских настроек."""

        current_amount = UserConfig.get_by_owner(telegram_id)
        if current_amount is None or current_amount.invoice_amount is None:
            self.telegram.send_message(telegram_id, "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму».")
            return

        self.telegram.send_message(telegram_id, f"💶 Текущая сумма Salary Invoice: {current_amount.invoice_amount} EUR")

    def bank_confirmation(self, telegram_id: int) -> None:
        """Генерирует подтверждение для банка и отправляет его пользователю."""

        LOGGER.info("Bank confirmation generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.GENERATING_BANK_CONFIRMATION)

        bank_confirmation_path = generate_bank_confirmation(telegram_id)
        LOGGER.info("Bank confirmation generated for Telegram user %s", telegram_id)
        self.telegram.send_document(telegram_id, bank_confirmation_path)

    def conversion_order(self, telegram_id: int) -> None:
        """Генерирует Conversion Order для текущего пользователя."""

        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.invoice_amount is None:
            LOGGER.warning("Conversion order generation blocked by missing invoice amount for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, "💰 Сумма Salary Invoice не указана.\nИспользуйте «Указать сумму».")
            return

        try:
            LOGGER.info("Conversion order generation requested by Telegram user %s", telegram_id)
            conversion_order_pdf_path = generate_conversion_order_pdf(
                telegram_id=telegram_id,
                amount=str(config.invoice_amount),
            )
        except ValueError as error:
            LOGGER.warning("Conversion order generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error))
            return
        LOGGER.info("Conversion order generated for Telegram user %s", telegram_id)
        self.telegram.send_document(telegram_id, conversion_order_pdf_path)
        self.telegram.send_message(telegram_id, Message.CONVERSION_ORDER_GENERATED)
