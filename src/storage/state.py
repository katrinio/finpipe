"""Файловое хранение небольшого состояния Telegram-бота."""

from __future__ import annotations

import json

from src.constants import Dir

STATE_PATH = Dir.STORAGE_DIR / "state.json"
LAST_UPDATE_ID_KEY = "last_update_id"


def load_last_update_id() -> int | None:
    """Загружает последний обработанный update_id, если он сохранён."""

    if not STATE_PATH.exists():
        return None

    with STATE_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    value = data.get(LAST_UPDATE_ID_KEY)
    return int(value) if value is not None else None


def save_last_update_id(update_id: int) -> None:
    """Сохраняет последний обработанный update_id."""

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps({LAST_UPDATE_ID_KEY: update_id}, ensure_ascii=False),
        encoding="utf-8",
    )
