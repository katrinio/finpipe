"""Сборка storage-зависимостей для composition root workflow-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.migration import JsonToSQLiteMigrator
from src.storage.repositories import InvoiceHistoryRepository, ProcessedMessageRepository
from src.storage.sqlalchemy_repositories import (
    SQLAlchemyInvoiceHistoryRepository,
    SQLAlchemyProcessedMessageRepository,
)


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор репозиториев для прикладного слоя."""

    invoice_history: InvoiceHistoryRepository
    processed_messages: ProcessedMessageRepository


DEFAULT_DB_PATH = Dir.STORAGE_DB
DEFAULT_HISTORY_JSON_PATH = Dir.STORAGE_HISTORY_JSON
DEFAULT_PROCESSED_MESSAGES_JSON_PATH = Dir.STORAGE_PROCESSED_MESSAGES_JSON


def build_storage_dependencies(
    db_path: Path = DEFAULT_DB_PATH,
    history_json_path: Path = DEFAULT_HISTORY_JSON_PATH,
    processed_messages_json_path: Path = DEFAULT_PROCESSED_MESSAGES_JSON_PATH,
) -> StorageDependencies:
    """Инициализирует БД и возвращает репозитории для workflow-композиции."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    invoice_history = SQLAlchemyInvoiceHistoryRepository(database.session)
    processed_messages = SQLAlchemyProcessedMessageRepository(database.session)

    JsonToSQLiteMigrator(
        database=database,
        invoice_history_path=history_json_path,
        processed_messages_path=processed_messages_json_path,
        invoice_repository=invoice_history,
        processed_message_repository=processed_messages,
    ).migrate()

    return StorageDependencies(
        invoice_history=invoice_history,
        processed_messages=processed_messages,
    )
