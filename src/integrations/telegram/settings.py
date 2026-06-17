"""Настройки Telegram-бота."""

from src.utils.credentials import EnvVar


class TelegramSettings:
    """Telegram-specific runtime settings."""

    @staticmethod
    def get_monitoring_chat_id() -> int | None:
        monitoring_chat_id = EnvVar.get_optional_env("MONITORING_CHAT_ID", "").strip()
        if not monitoring_chat_id:
            return None
        return int(monitoring_chat_id)
