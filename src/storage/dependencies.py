"""Сборка storage-зависимостей для composition root workflow-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.repositories import InvoiceHistoryRepository, ProcessedMessageRepository
from src.storage.repositories.sqlalchemy_repositories import (
    SQLAlchemyInvoiceHistoryRepository,
    SQLAlchemyProcessedMessageRepository,
)


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор репозиториев для прикладного слоя."""

    invoice_history: InvoiceHistoryRepository
    processed_messages: ProcessedMessageRepository


DEFAULT_DB_PATH = Dir.STORAGE_DB


def build_storage_dependencies(
    db_path: Path = DEFAULT_DB_PATH,
) -> StorageDependencies:
    """Инициализирует БД и возвращает репозитории для workflow-композиции."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    invoice_history = SQLAlchemyInvoiceHistoryRepository(database.session)
    processed_messages = SQLAlchemyProcessedMessageRepository(database.session)

    return StorageDependencies(
        invoice_history=invoice_history,
        processed_messages=processed_messages,
    )
