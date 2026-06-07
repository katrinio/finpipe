"""Совместимый re-export ORM-моделей storage-слоя.

TODO: удалить после перевода всех импортов на `src.storage.orm`.
"""

from src.storage.orm import AppliedMigration, BaseStorage, HistoryRecord, ProcessedMessage

Base = BaseStorage

__all__ = [
    "AppliedMigration",
    "Base",
    "BaseStorage",
    "HistoryRecord",
    "ProcessedMessage",
]
