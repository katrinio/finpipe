from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import Cmd
from src.storage.repositories.telegram_update_repository import build_telegram_update_storage
from src.utils.credentials import LOGGER
from src.workflows.generate_invoice_and_send import generate_and_send_invoice


def handle_message(text: str) -> bool:
    telegram = TelegramClient()

    match text:
        case Cmd.STATUS:
            telegram.send_message("Finpipe is running")
            return True
        case Cmd.HELP:
            telegram.send_message("/status - bot status\n/help - available commands/health - bot health")
            return True
        case Cmd.HEALTH:
            try:
                telegram.healthcheck()
                telegram.send_message("✅ Telegram API OK")
            except Exception:
                telegram.send_message("❌ Telegram API ERROR")
                return False
            return True
        case Cmd.INVOICE:
            telegram.send_message("⏳ Generating invoice...")
            try:
                generate_and_send_invoice()
                telegram.send_message("✅ Invoice sent")
            except Exception as error:
                telegram.send_message(f"❌ Invoice generation failed:\n{error}")
                return False
            return True
        case _:
            telegram.send_message("... try another command")
            return True


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
    # помечаем накопившиеся сообщения обработанными и не выполняем старые команды
    if last_processed_update_id is None:
        for update in result:
            mark_update_as_processed(storage, update)
        return

    for update in result:
        message = update.get("message")
        if not message:
            continue

        text = message.get("text")
        if not text:
            continue

        try:
            handle_message(text)
            mark_update_as_processed(storage, update)
        except Exception:
            LOGGER.exception("Failed to process Telegram update %s", update["update_id"])


def mark_update_as_processed(storage, update: dict) -> None:
    """Обрабатывает один update и помечает его только после успеха."""

    update_id = update.get("update_id")
    if not isinstance(update_id, int):
        return

    if storage.is_processed(update_id):
        return

    message = update.get("message")
    if not message:
        return

    text = message.get("text")
    if not text:
        return

    if handle_message(text):
        storage.mark_processed(update_id)


# TODO: убрать после отладки
if __name__ == "__main__":
    poll()
