"""Локальный Telegram listener и обработчик команд."""

from __future__ import annotations

import time
from collections.abc import Callable

from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import (
    BotInfo,
    Cmd,
    build_help_message,
    format_last_action,
    format_whoami,
)
from src.storage.dependencies import (
    StorageDependencies,
    build_storage_dependencies,
)
from src.storage.repositories.telegram_update_repository import (
    build_telegram_update_storage,
)
from src.utils.credentials import LOGGER
from src.workflows.generate_invoice_and_send import (
    generate_and_send_invoice,
)


class TelegramBot:
    """Telegram listener и обработчик команд."""

    def __init__(self, storage_dependencies: StorageDependencies) -> None:
        self.telegram = TelegramClient()
        self.dependencies = storage_dependencies
        self.update_storage = build_telegram_update_storage(Dir.STORAGE_DB)

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
            return self._mark_initial_updates_as_processed(result)

        for update in result:
            self._process_update(update)

        return len(result)

    def handle_message(self, text: str, telegram_id: int | None, username: str | None) -> bool:
        """Выполняет команду Telegram."""

        handlers: dict[str, Callable[[], None]] = {
            Cmd.STATUS: self._status,
            Cmd.HELP: self._help,
            Cmd.HEALTH: self._health,
            Cmd.INVOICE: self._invoice,
            Cmd.ABOUT: self._about,
            Cmd.WHOAMI: lambda: self._whoami(telegram_id, username),
            Cmd.LAST_ACTION: self._last_action,
        }

        try:
            handler = handlers.get(text)

            if handler is None:
                self.telegram.send_message(BotInfo.NO_SUCH_COMMAND)
            else:
                handler()

        except Exception as error:
            LOGGER.exception("Command failed: %s", text)
            self.telegram.send_message(f"❌ Command {text} failed:\n{error}")

            return False

        return True

    def _process_update(self, update: dict) -> None:
        """Обрабатывает один Telegram update."""

        message = update.get("message")

        if not message:
            return

        text = message.get("text")

        if not text:
            return

        from_user = message.get("from", {})

        telegram_id = from_user.get("id")
        username = from_user.get("username")

        if telegram_id is None:
            return

        update_id = update["update_id"]

        if not self._is_authorized(telegram_id):
            LOGGER.warning("Access denied for Telegram user %s (@%s)", telegram_id, username)
            self.telegram.send_message(BotInfo.ACCESS_DENIED)
            return

        LOGGER.info("Processing Telegram command: %s", text)

        if self.handle_message(text=text, telegram_id=telegram_id, username=username):
            self.update_storage.mark_processed(update_id)

    def _is_authorized(self, telegram_id: int) -> bool:
        """Проверяет доступ пользователя."""

        return self.dependencies.allowed_users.get_by_telegram_id(telegram_id) is not None

    def _mark_initial_updates_as_processed(self, updates: list[dict]) -> int:
        """Первый запуск: сохраняем старые updates без обработки."""

        for update in updates:
            self.update_storage.mark_processed(update["update_id"])
        return len(updates)

    def _status(self) -> None:
        self.telegram.send_message(BotInfo.PROJECT_RUNNING)

    def _help(self) -> None:
        self.telegram.send_message(build_help_message())

    def _health(self) -> None:
        self.telegram.healthcheck()
        self.telegram.send_message(BotInfo.TG_API_OK)

    def _invoice(self) -> None:
        self.telegram.send_message(BotInfo.GENERATING_INVOICE)
        generate_and_send_invoice()
        self.telegram.send_message(BotInfo.INVOICE_SENT)

    def _about(self) -> None:
        self.telegram.send_message(BotInfo.ABOUT)

    def _whoami(self, telegram_id: int | None, username: str | None) -> None:
        self.telegram.send_message(format_whoami(telegram_id, username))

    def _last_action(self) -> None:
        actions = self.dependencies.audit_log.list_recent(1)
        if not actions:
            self.telegram.send_message(BotInfo.NO_AUDIT_LOG_RECORDS)
            return

        self.telegram.send_message(format_last_action(actions[0]))


if __name__ == "__main__":
    bot = TelegramBot(build_storage_dependencies(Dir.STORAGE_DB))

    LOGGER.info("Starting Telegram listener loop")
    while True:
        try:
            bot.poll()
        except Exception:
            "Telegram listener iteration failed"

        time.sleep(5)
