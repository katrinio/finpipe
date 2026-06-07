"""Совместимый модуль-обёртка над SQLAlchemy storage.

TODO: удалить после отказа от legacy-имени `sqlite.py`.
"""

from src.storage.database import Database as SQLiteDatabase
from src.storage.database import build_sqlite_url
from src.storage.sqlalchemy_repositories import (
    SQLAlchemyInvoiceHistoryRepository as SQLiteInvoiceHistoryRepository,
)
from src.storage.sqlalchemy_repositories import (
    SQLAlchemyProcessedMessageRepository as SQLiteProcessedMessageRepository,
)

__all__ = [
    "SQLiteDatabase",
    "SQLiteInvoiceHistoryRepository",
    "SQLiteProcessedMessageRepository",
    "build_sqlite_url",
]
