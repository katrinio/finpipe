from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid
from src.integrations.telegram.settings import TelegramSettings
from src.utils.credentials import LOGGER


class MonitoringHandler:
    """Обрабатывает команды мониторингового чата. Alert-only бот."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def handle_message(self, text: str | None, chat_id: int | None, telegram_id: int | None, username: str | None) -> bool:
        monitoring_chat_id = TelegramSettings.get_monitoring_chat_id()
        if monitoring_chat_id is None or chat_id != monitoring_chat_id or text is None:
            return False

        try:
            command = self._normalize_command(text)
            if command == "/chatid":
                self.telegram.send_message(chat_id, format_chatid(chat_id))
            return True
        except Exception:
            LOGGER.exception("Monitoring command failed in chat %s", chat_id)
            return True

    @staticmethod
    def _normalize_command(text: str) -> str:
        return text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
