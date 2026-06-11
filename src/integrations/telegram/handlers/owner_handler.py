"""Команды владельца Telegram-бота."""

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm import AllowedUser


class OwnerHandlers:
    """Обрабатывает команды владельца бота."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def add_user(self, telegram_id: int, command: str, username: str | None) -> None:
        """Добавляет Telegram-пользователя в allowlist."""

        if not AllowedUser.is_owner(telegram_id):
            self.telegram.send_message(telegram_id, BotInfo.ACCESS_DENIED)
            return

        parts = command.split()
        if len(parts) != 2:
            self.telegram.send_message(telegram_id, "Использование: /add_user <telegram_id>")
            return

        try:
            allowed_telegram_id = int(parts[1])
        except ValueError:
            self.telegram.send_message(telegram_id, "Использование: /add_user <telegram_id>")
            return

        AllowedUser.upsert(telegram_id=allowed_telegram_id, username=username)
        self.telegram.send_message(telegram_id, "✅ Пользователь добавлен.")
