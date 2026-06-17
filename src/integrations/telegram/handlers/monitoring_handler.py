from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid, format_recent_errors, format_stats
from src.integrations.telegram.settings import TelegramSettings
from src.integrations.telegram.ui.messages import CommonMessages
from src.services.monitoring.event_analytics import EventAnalytics
from src.services.system_status.system_status_service import SystemStatusService
from src.utils.credentials import LOGGER


class MonitoringHandler:
    """Обрабатывает текстовые команды мониторингового чата."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def handle_message(self, text: str | None, chat_id: int | None, telegram_id: int | None, username: str | None) -> bool:
        """Обрабатывает /status, /health, /events, /errors и /chatid только в monitoring chat."""

        monitoring_chat_id = TelegramSettings.get_monitoring_chat_id()
        if monitoring_chat_id is None or chat_id != monitoring_chat_id or text is None:
            return False

        try:
            command = self._normalize_command(text)
            if command == "/status":
                self._status(chat_id)
                return True
            if command == "/health":
                self._health(chat_id)
                return True
            if command == "/events":
                self._events(chat_id)
                return True
            if command == "/errors":
                self._errors(chat_id)
                return True
            if command == "/chatid":
                self.telegram.send_message(chat_id, format_chatid(chat_id))
                return True

            LOGGER.info("Ignoring unknown monitoring command %r in chat %s", text, chat_id)
            return True
        except Exception:
            LOGGER.exception("Monitoring command failed in chat %s", chat_id)
            self.telegram.send_message(chat_id, CommonMessages.Errors.SYSTEM_ERROR)
            return True

    def _status(self, chat_id: int) -> None:
        status = SystemStatusService.get_status(chat_id)

        def icon(value: bool) -> str:
            return "✅" if value else "❌"

        message = (
            "📊 Finpipe status\n\n"
            "Profile:\n"
            f"{icon(status.company)} Company\n"
            f"{icon(status.bank_details)} Bank details\n"
            f"{icon(status.signature)} Signature\n\n"
            "Integrations:\n"
            f"{icon(status.gmail)} Gmail\n\n"
            "Documents:\n"
            f"{icon(status.bank_confirmation_available)} Bank Confirmation\n"
            f"{icon(status.invoice_available)} Salary Invoice\n"
            f"{icon(status.conversion_order_available)} Conversion Order"
        )
        self.telegram.send_message(chat_id, message)

    def _health(self, chat_id: int) -> None:
        self.telegram.healthcheck()
        self.telegram.send_message(chat_id, "✅ Telegram API is available")

    def _events(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(
            chat_id,
            format_stats(
                total_events=analytics.get_total_events(),
                event_counts=analytics.get_event_counts(),
                document_stats=analytics.get_document_generation_stats(),
                error_count=analytics.get_error_counts(),
                recent_error_count=len(analytics.get_recent_errors(limit=3)),
            ),
        )

    def _errors(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(chat_id, format_recent_errors(analytics.get_recent_errors(limit=10)))

    @staticmethod
    def _normalize_command(text: str) -> str:
        return text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
