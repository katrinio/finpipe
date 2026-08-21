import logging

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.document_menu import (
    build_invoice_menu,
)
from src.integrations.telegram.ui.messages import InvoiceMessages
from src.services.invoice.exceptions import InvoiceError
from src.services.monitoring.event_logger import EventLogger
from src.services.system_status.system_status_service import SystemStatusService
from src.storage.orm import UserConfig
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.workflows.run_invoice_delivery import generate_and_send_invoice

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

    def _invoice_readiness_error(self, telegram_id: int) -> str | None:
        status = SystemStatusService.get_status(telegram_id)
        if not status.company or not status.bank_details:
            return InvoiceMessages.Validation.PROFILE_REQUIRED
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.invoice_amount_eur is None:
            return InvoiceMessages.Validation.NO_INVOICE_AMOUNT
        return None
