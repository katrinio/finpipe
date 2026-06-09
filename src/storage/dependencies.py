"""Сборка storage-зависимостей для composition root workflow-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.orm import AuditLog, HistoryRecord, ProcessedMessage


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор persistence-моделей для прикладного слоя."""

    audit_log: type[AuditLog]
    invoice_history: type[HistoryRecord]
    processed_messages: type[ProcessedMessage]


DEFAULT_DB_PATH = Dir.STORAGE_DB


def build_storage_dependencies(db_path: Path = DEFAULT_DB_PATH) -> StorageDependencies:
    """Инициализирует БД и возвращает репозитории для workflow-композиции."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    return StorageDependencies(
        audit_log=AuditLog,
        invoice_history=HistoryRecord,
        processed_messages=ProcessedMessage,
    )
