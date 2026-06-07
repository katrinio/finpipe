from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import BotInfo, Cmd, build_help_message
from src.storage.repositories.telegram_update_repository import build_telegram_update_storage
from src.utils.credentials import LOGGER
from src.workflows.generate_invoice_and_send import generate_and_send_invoice


def handle_message(text: str) -> bool:
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


def poll() -> None:
    telegram = TelegramClient()
    storage = build_telegram_update_storage(Dir.STORAGE_DB)
    last_processed_update_id = storage.get_last_processed_update_id()

    offset = last_processed_update_id + 1 if last_processed_update_id is not None else None

    updates = telegram.get_updates(offset=offset)

    result = updates.get("result", [])
    if not result:
        return

    # Первый запуск:
    # не выполняем старые команды, только сохраняем их как обработанные.
    if last_processed_update_id is None:
        for update in result:
            storage.mark_processed(update["update_id"])
        return

    for update in result:
        message = update.get("message")
        if not message:
            continue

        text = message.get("text")
        if not text:
            continue

        update_id = update["update_id"]

        try:
            LOGGER.info("Processing Telegram command: %s", text)
            if handle_message(text):
                storage.mark_processed(update_id)
        except Exception as error:
            LOGGER.exception("Failed to process Telegram update %s, Error: %s", update_id, error)


# TODO: убрать после отладки
if __name__ == "__main__":
    handle_message(Cmd.STATUS)
    handle_message(Cmd.HEALTH)
    handle_message(Cmd.INVOICE)
    handle_message(Cmd.ABOUT)
    handle_message(Cmd.HELP)
