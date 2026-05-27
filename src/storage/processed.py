import json
from pathlib import Path

FILE_PATH = Path("processed_messages.json")


def load_processed_messages() -> set[str]:
    if not FILE_PATH.exists():
        return set()

    with open(FILE_PATH, encoding="utf-8") as file:
        data = json.load(file)

    return set(data.get("processed_messages", []))


def save_processed_messages(ids: set[str]) -> None:
    data = {
        "processed_messages": list(ids)
    }

    with open(FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def is_processed(message_id: str) -> bool:
    return message_id in load_processed_messages()


def mark_as_processed(message_id: str) -> None:
    ids = load_processed_messages()
    ids.add(message_id)
    save_processed_messages(ids)
