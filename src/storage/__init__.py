"""Хранилища локального состояния и истории запусков."""

from .processed_messages import (
    clear_processed_history,
    is_processed,
    load_processed_messages,
    mark_as_processed,
    save_processed_messages,
)

__all__ = [
    "clear_processed_history",
    "is_processed",
    "load_processed_messages",
    "mark_as_processed",
    "save_processed_messages",
]
