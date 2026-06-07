from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import Cmd
from src.storage.state import load_last_update_id, save_last_update_id


def handle_message(text: str) -> None:
    telegram = TelegramClient()

    match text:
        case Cmd.STATUS:
            telegram.send_message("Finpipe is running")
        case _:
            telegram.send_message("... try another command")


def poll() -> None:
    telegram = TelegramClient()
    last_update_id = load_last_update_id()
    offset = last_update_id + 1 if last_update_id is not None else None
    updates = telegram.get_updates(offset=offset)

    result = updates.get("result", [])
    if not result:
        return

    max_update_id = last_update_id

    for update in result:
        update_id = update.get("update_id")
        if isinstance(update_id, int) and (max_update_id is None or update_id > max_update_id):
            max_update_id = update_id

        message = update.get("message")
        if not message:
            continue

        text = message.get("text")
        if not text:
            continue

        handle_message(text)

    if max_update_id is not None:
        save_last_update_id(max_update_id)


# TODO: убрать после отладки
if __name__ == "__main__":
    poll()
