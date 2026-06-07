"""Совместимый фасад processed messages поверх нового repository-слоя."""

from __future__ import annotations

import logging

from src.constants import Dir
from src.storage.dependencies import build_storage_dependencies
from src.storage.repositories import ProcessedMessageRepository

LOGGER = logging.getLogger(__name__)
FILE_PATH = Dir.STORAGE_PROCESSED_MESSAGES_JSON
DB_PATH = Dir.STORAGE_DB


def _repository() -> ProcessedMessageRepository:
    return build_storage_dependencies(
        db_path=DB_PATH,
        processed_messages_json_path=FILE_PATH,
    ).processed_messages


def load_processed_messages() -> set[str]:
    """Загружает набор уже обработанных message_id."""

    return set(_repository().list_message_ids())


def save_processed_messages(ids: set[str]) -> None:
    """Полностью сохраняет текущий набор обработанных писем в SQLite."""

    _repository().replace_all(ids)
    LOGGER.debug("Saved %s processed message ids to %s", len(ids), DB_PATH)


def is_processed(message_id: str) -> bool:
    """Проверяет, обрабатывалось ли письмо ранее."""

    return _repository().is_processed(message_id)


def mark_as_processed(message_id: str) -> None:
    """Помечает письмо банка как обработанное."""

    _repository().mark_as_processed(message_id)
    LOGGER.debug("Marked message as processed: %s", message_id)


def clear_processed_history() -> None:
    """Полностью очищает историю обработанных писем."""

    _repository().clear()
    LOGGER.debug("Cleared processed message history in %s", DB_PATH)
