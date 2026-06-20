import subprocess

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid, format_recent_errors, format_recent_events, format_stats
from src.integrations.telegram.settings import TelegramSettings
from src.integrations.telegram.ui.messages import CommonMessages
from src.services.monitoring.event_analytics import EventAnalytics
from src.services.system_status.system_status_service import SystemStatusService
from src.utils.credentials import LOGGER, EnvVar


class MonitoringHandler:
    """Обрабатывает текстовые команды мониторингового чата."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def handle_message(self, text: str | None, chat_id: int | None, telegram_id: int | None, username: str | None) -> bool:
        """Обрабатывает /status, /health, /events, /errors, /stats и /chatid только в monitoring chat."""

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
            if command == "/stats":
                self._stats(chat_id)
                return True
            if command == "/chatid":
                self.telegram.send_message(chat_id, format_chatid(chat_id))
                return True
            if command.startswith("/logs"):
                self._logs(chat_id, text)
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

    def _logs(self, chat_id: int, text: str) -> None:
        parts = text.strip().split()
        try:
            tail = int(parts[1]) if len(parts) > 1 else 50
            tail = max(1, min(tail, 200))
        except ValueError:
            self.telegram.send_message(chat_id, "⚠️ Использование: /logs [N] — последние N строк (макс. 200)")
            return

        container = EnvVar.get_optional_env("CONTAINER_NAME", "finpipe-bot")
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            output = (result.stdout + result.stderr).strip()
        except FileNotFoundError:
            self.telegram.send_message(chat_id, "❌ docker не найден — сокет смонтирован?")
            return
        except subprocess.TimeoutExpired:
            self.telegram.send_message(chat_id, "❌ Таймаут при получении логов")
            return

        if not output:
            self.telegram.send_message(chat_id, "📋 Логи пусты")
            return

        header = f"📋 Последние {tail} строк [{container}]\n\n"
        # Telegram limit: 4096 chars
        body = output[-(4096 - len(header)) :]
        self.telegram.send_message(chat_id, f"{header}{body}")

    def _health(self, chat_id: int) -> None:
        self.telegram.healthcheck()
        self.telegram.send_message(chat_id, "✅ Telegram API is available")

    def _events(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(chat_id, format_recent_events(analytics.get_recent_events(limit=10)))

    def _errors(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(chat_id, format_recent_errors(analytics.get_recent_errors(limit=10)))

    def _stats(self, chat_id: int) -> None:
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

    @staticmethod
    def _normalize_command(text: str) -> str:
        return text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
