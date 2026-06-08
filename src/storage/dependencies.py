"""Сборка storage-зависимостей для composition root workflow-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.audit_log_repository import AuditLogRepository, SQLAlchemyAuditLogRepository


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор репозиториев для прикладного слоя."""

    audit_log: AuditLogRepository


DEFAULT_DB_PATH = Dir.STORAGE_DB


def build_storage_dependencies(db_path: Path = DEFAULT_DB_PATH) -> StorageDependencies:
    """Инициализирует БД и возвращает репозитории для workflow-композиции."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    audit_log = SQLAlchemyAuditLogRepository(database.session)

    return StorageDependencies(audit_log=audit_log)
