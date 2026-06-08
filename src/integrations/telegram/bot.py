"""Локальный Telegram listener и обработчик команд."""

from __future__ import annotations

import time

from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message
from src.storage.dependencies import build_storage_dependencies
from src.storage.repositories.telegram_update_repository import build_telegram_update_storage
from src.utils.credentials import LOGGER
from src.workflows.generate_invoice_and_send import generate_and_send_invoice


def _format_whoami(telegram_id: int | None, username: str | None) -> str:
    return f"{BotInfo.WHOAMI_PREFIX}\ntelegram_id: {telegram_id}\nusername: {username or 'unknown'}"


def handle_message(text: str, telegram_id: int | None = None, username: str | None = None) -> bool:
    telegram = TelegramClient()

    try:
        match text:
            case Cmd.STATUS:
                telegram.send_message(BotInfo.PROJECT_RUNNING)
                return True
            case Cmd.HELP:
                telegram.send_message(build_help_message())
                return True
            case Cmd.HEALTH:
                telegram.healthcheck()
                telegram.send_message(BotInfo.TG_API_OK)
                return True
            case Cmd.INVOICE:
                telegram.send_message(BotInfo.GENERATING_INVOICE)
                generate_and_send_invoice()
                telegram.send_message(BotInfo.INVOICE_SENT)
                return True
            case Cmd.WHOAMI:
                telegram.send_message(_format_whoami(telegram_id, username))
                return True
            case Cmd.ABOUT:
                telegram.send_message(BotInfo.ABOUT)
                return True
            case _:
                telegram.send_message(BotInfo.NO_SUCH_COMMAND)
                return True

    except Exception as error:
        LOGGER.exception("Command failed: %s", text)
        telegram.send_message(f"❌ Command {text} failed:\n{error}")
        return False


def _mark_initial_updates_as_processed(storage, result: list[dict]) -> int:
    for update in result:
        storage.mark_processed(update["update_id"])
    return len(result)


def _is_authorized(user_config_repository, telegram_id: int) -> bool:
    return user_config_repository.get_by_telegram_id(telegram_id) is not None


def _process_update(update: dict, telegram: TelegramClient, storage, user_config_repository) -> None:
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

    if not _is_authorized(user_config_repository, telegram_id):
        LOGGER.warning("Access denied for Telegram user %s (@%s)", telegram_id, username)
        telegram.send_message(BotInfo.ACCESS_DENIED)
        return

    try:
        LOGGER.info("Processing Telegram command: %s", text)
        if handle_message(text, telegram_id=telegram_id, username=username):
            storage.mark_processed(update_id)
    except Exception as error:
        LOGGER.exception("Failed to process Telegram update %s, Error: %s", update_id, error)


def poll() -> int:
    telegram = TelegramClient()
    storage_dependencies = build_storage_dependencies(Dir.STORAGE_DB)
    storage = build_telegram_update_storage(Dir.STORAGE_DB)
    last_processed_update_id = storage.get_last_processed_update_id()

    offset = last_processed_update_id + 1 if last_processed_update_id is not None else None

    updates = telegram.get_updates(offset=offset)

    result = updates.get("result", [])
    LOGGER.info("Telegram poll returned %s updates", len(result))
    if not result:
        return 0

    # Первый запуск:
    # не выполняем старые команды, только сохраняем их как обработанные.
    if last_processed_update_id is None:
        return _mark_initial_updates_as_processed(storage, result)

    for update in result:
        _process_update(update, telegram, storage, storage_dependencies.user_config)

    return len(result)


if __name__ == "__main__":
    LOGGER.info("Starting Telegram listener loop")
    while True:
        try:
            poll()
        except Exception:
            LOGGER.exception("Telegram listener iteration failed")
        time.sleep(5)
