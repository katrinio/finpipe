import subprocess

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid, format_recent_errors
from src.integrations.telegram.settings import TelegramSettings
from src.integrations.telegram.ui.messages import CommonMessages
from src.services.monitoring.event_analytics import EventAnalytics
from src.utils.credentials import LOGGER, EnvVar


class MonitoringHandler:
    """Обрабатывает текстовые команды мониторингового чата."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    _HELP = (
        "📖 Доступные команды:\n\n"
        "/errors — последние 10 ошибок\n"
        "/logs [N] — последние N строк из контейнера (по умолчанию 50)\n"
        "/chatid — ID этого чата\n"
        "/help — список команд"
    )

    def handle_message(self, text: str | None, chat_id: int | None, telegram_id: int | None, username: str | None) -> bool:
        """Обрабатывает команды мониторингового чата."""

        monitoring_chat_id = TelegramSettings.get_monitoring_chat_id()
        if monitoring_chat_id is None or chat_id != monitoring_chat_id or text is None:
            return False

        try:
            command = self._normalize_command(text)
            if command == "/errors":
                self._errors(chat_id)
                return True
            if command == "/chatid":
                self.telegram.send_message(chat_id, format_chatid(chat_id))
                return True
            if command.startswith("/logs"):
                self._logs(chat_id, text)
                return True
            if command == "/help":
                self.telegram.send_message(chat_id, self._HELP)
                return True

            if text.startswith("/"):
                self.telegram.send_message(chat_id, f"❓ Неизвестная команда.\n\n{self._HELP}")
            return True
        except Exception:
            LOGGER.exception("Monitoring command failed in chat %s", chat_id)
            self.telegram.send_message(chat_id, CommonMessages.Errors.SYSTEM_ERROR)
            return True

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
        body = output[-(4096 - len(header)) :]
        self.telegram.send_message(chat_id, f"{header}{body}")

    def _errors(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(chat_id, format_recent_errors(analytics.get_recent_errors(limit=10)))

    @staticmethod
    def _normalize_command(text: str) -> str:
        return text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
