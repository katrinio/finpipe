"""Сборка storage-зависимостей для composition root workflow-слоя."""

from dataclasses import dataclass
from pathlib import Path

from src.storage.config import DatabaseConfig
from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm import AuditLog, ProcessedMessage
from src.storage.orm.database import Database
from src.storage.orm.system.document_generation_history import DocumentGenerationHistory


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор persistence-моделей для прикладного слоя."""

    audit_log: type[AuditLog]
    document_generation_history: type[DocumentGenerationHistory]
    processed_messages: type[ProcessedMessage]


def build_storage_dependencies(database_url: str | Path | None = None) -> StorageDependencies:
    """Применяет миграции и возвращает репозитории для workflow-композиции."""

    resolved_database_url = DatabaseConfig.get_database_url(database_url)
    run_alembic_upgrade_head(resolved_database_url)
    database = Database(resolved_database_url)
    database.bind_models()

    return StorageDependencies(
        audit_log=AuditLog,
        document_generation_history=DocumentGenerationHistory,
        processed_messages=ProcessedMessage,
    )
