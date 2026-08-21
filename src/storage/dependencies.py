"""Сборка storage-зависимостей для composition root workflow-слоя."""

from dataclasses import dataclass

from src.storage.migrations import run_alembic_upgrade_head
from src.storage.orm import AuditLog
from src.storage.orm.database import Database
from src.storage.orm.system.document_generation_history import DocumentGenerationHistory


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор persistence-моделей для прикладного слоя."""

    audit_log: type[AuditLog]
    document_generation_history: type[DocumentGenerationHistory]


def build_storage_dependencies() -> StorageDependencies:
    """Применяет миграции и возвращает репозитории для workflow-композиции."""

    run_alembic_upgrade_head()
    database = Database.from_env()
    database.bind_models()

    return StorageDependencies(
        audit_log=AuditLog,
        document_generation_history=DocumentGenerationHistory,
    )
