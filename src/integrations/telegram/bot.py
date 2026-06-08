"""Локальный Telegram listener и обработчик команд."""

from __future__ import annotations

import time

from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo
from src.integrations.telegram.handlers import TelegramHandlers
from src.storage.dependencies import (
    StorageDependencies,
    build_storage_dependencies,
)
from src.storage.orm import AllowedUser
from src.storage.repositories.telegram_update_repository import (
    build_telegram_update_storage,
)
from src.utils.credentials import LOGGER


class TelegramBot:
    """Telegram listener и обработчик команд."""

    def __init__(self, storage_dependencies: StorageDependencies) -> None:
        self.telegram = TelegramClient()
        self.dependencies = storage_dependencies
        self.update_storage = build_telegram_update_storage(Dir.STORAGE_DB)
        self.handlers = TelegramHandlers(
            telegram=self.telegram,
            audit_log=self.dependencies.audit_log,
        )

    def poll(self) -> int:
        """Получает и обрабатывает новые Telegram updates."""

        last_processed_update_id = self.update_storage.get_last_processed_update_id()

        offset = last_processed_update_id + 1 if last_processed_update_id is not None else None

        updates = self.telegram.get_updates(offset=offset)

        result = updates.get("result", [])
        LOGGER.info("Telegram poll returned %s updates", len(result))

        if not result:
            return 0

        if last_processed_update_id is None:
            return self.mark_initial_updates_as_processed(result)

        for update in result:
            self.process_update(update)

        return len(result)

    def extract_message_data(self, update: dict) -> tuple[str, int, str | None] | None:
        """Извлекает данные пользователя и команду из update."""

        message = update.get("message")
        if not message:
            return None

        text = message.get("text")
        user = message.get("from", {})

        telegram_id = user.get("id")
        if not text or telegram_id is None:
            return None

        return text, telegram_id, user.get("username")

    def process_update(self, update: dict) -> None:
        """Обрабатывает один Telegram update."""

        data = self.extract_message_data(update)
        if data is None:
            return

        text, telegram_id, username = data

        if not self.is_authorized(telegram_id):
            LOGGER.warning("Access denied for Telegram user %s (@%s)", telegram_id, username)
            self.telegram.send_message(BotInfo.ACCESS_DENIED)
            return

        LOGGER.info("Processing Telegram command: %s", text)

        if self.handlers.handle_message(text=text, telegram_id=telegram_id, username=username):
            self.update_storage.mark_processed(update["update_id"])

    def mark_initial_updates_as_processed(self, updates: list[dict]) -> int:
        """Первый запуск: сохраняем старые updates без обработки."""
        for update in updates:
            self.update_storage.mark_processed(update["update_id"])
        return len(updates)

    def is_authorized(self, telegram_id: int) -> bool:
        """Проверяет доступ пользователя."""
        return AllowedUser.get_by_telegram_id(telegram_id) is not None


if __name__ == "__main__":
    bot = TelegramBot(build_storage_dependencies(Dir.STORAGE_DB))

    LOGGER.info("Starting Telegram listener loop")
    while True:
        try:
            bot.poll()
        except Exception:
            LOGGER.exception("Telegram listener iteration failed")

        time.sleep(5)
