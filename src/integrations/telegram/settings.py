"""Настройки Telegram-бота."""

from __future__ import annotations

from src.utils.credentials import EnvVar


class TelegramSettings:
    """Telegram-specific runtime settings."""

    @classmethod
    def owner_telegram_id(cls) -> int:
        owner_value = EnvVar.get_optional_env(
            "BOT_OWNER_TELEGRAM_ID",
            EnvVar.get_optional_env("TELEGRAM_ADMIN_ID", "0"),
        )
        return int(owner_value)
