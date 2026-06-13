"""Сборка storage-зависимостей для composition root workflow-слоя."""

from dataclasses import dataclass
from pathlib import Path

from src.constants import Dir
from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm import AuditLog, ProcessedMessage
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.system.document_generation_history import DocumentGenerationHistory


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор persistence-моделей для прикладного слоя."""

    audit_log: type[AuditLog]
    document_generation_history: type[DocumentGenerationHistory]
    processed_messages: type[ProcessedMessage]


DEFAULT_DB_PATH = Dir.STORAGE_DB


def build_storage_dependencies(db_path: Path = DEFAULT_DB_PATH) -> StorageDependencies:
    """Применяет миграции и возвращает репозитории для workflow-композиции."""

    run_alembic_upgrade_head(db_path)
    database = Database(build_sqlite_url(db_path))
    database.bind_models()

    return StorageDependencies(
        audit_log=AuditLog,
        document_generation_history=DocumentGenerationHistory,
        processed_messages=ProcessedMessage,
    )
