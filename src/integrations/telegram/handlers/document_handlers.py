import logging

from src.constants import Message
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm import UserConfig
from src.workflows.run_invoice_delivery import generate_and_send_invoice
from src.workflows.tasks.fill_bank_pdf import fill_bank_pdf_with_data
from src.workflows.tasks.generate_transfer_request import generate_transfer_request_pdf

LOGGER = logging.getLogger(__name__)


class DocumentHandlers:
    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def start_invoice_amount_input(self, telegram_id: int) -> None:
        UserStateService.set_state(telegram_id, UserState.WAITING_INVOICE_AMOUNT)
        self.telegram.send_message(telegram_id, "💰 Введите сумму Invoice:")

    def handle_invoice_amount_input(self, telegram_id: int, text: str | None) -> None:
        if text is None or not text.isdigit() or int(text) <= 0:
            self.telegram.send_message(
                telegram_id,
                "❌ Сумма должна содержать только цифры.\nПример: 1500",
            )
            return

        amount = int(text)
        UserConfig.upsert(telegram_id=telegram_id, invoice_amount=amount)
        UserStateService.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, f"✅ Сумма Invoice сохранена: {amount} EUR")

    def invoice(self, telegram_id: int) -> None:
        LOGGER.info("Invoice generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.GENERATING_INVOICE)
        try:
            generate_and_send_invoice(telegram_id)
        except ValueError as error:
            LOGGER.warning("Invoice generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error))
            return
        LOGGER.info("Invoice generated for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.INVOICE_SENT)

    def get_invoice_amount(self, telegram_id: int) -> None:
        current_amount = UserConfig.get_by_owner(telegram_id)
        if current_amount is None or current_amount.invoice_amount is None:
            self.telegram.send_message(telegram_id, "💰 Сумма не задана.\nИспользуйте «Указать сумму».")
            return

        self.telegram.send_message(telegram_id, f"💶 Текущая сумма: {current_amount.invoice_amount} EUR")

    def bank(self, telegram_id: int) -> None:
        LOGGER.info("Bank PDF generation requested by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.FILL_BANK_PDF)

        bank_pdf_path = fill_bank_pdf_with_data(telegram_id)
        LOGGER.info("Bank PDF generated for Telegram user %s", telegram_id)
        self.telegram.send_document(telegram_id, bank_pdf_path)

    def transfer_request(self, telegram_id: int) -> None:
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.invoice_amount is None:
            LOGGER.warning("Transfer request generation blocked by missing invoice amount for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, "💰 Сумма Invoice не указана.\nИспользуйте «Указать сумму».")
            return

        try:
            LOGGER.info("Transfer request generation requested by Telegram user %s", telegram_id)
            transfer_request_pdf_path = generate_transfer_request_pdf(
                telegram_id=telegram_id,
                amount=str(config.invoice_amount),
            )
        except ValueError as error:
            LOGGER.warning("Transfer request generation failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, str(error))
            return
        LOGGER.info("Transfer request generated for Telegram user %s", telegram_id)
        self.telegram.send_document(telegram_id, transfer_request_pdf_path)
        self.telegram.send_message(telegram_id, Message.TRANSACTION_REQUEST_GENERATED)
