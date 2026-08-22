"""Настройки Telegram-бота."""

from src.utils.credentials import EnvVar


class TelegramSettings:
    """Telegram-specific runtime settings."""

    @staticmethod
    def get_owner_telegram_id() -> int:
        return int(EnvVar.get_required_env("BOT_OWNER_TELEGRAM_ID"))
