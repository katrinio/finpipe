"""Сборка storage-зависимостей для composition root workflow-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.constants import Dir
from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.allowed_user_repository import AllowedUserRepository, SQLAlchemyAllowedUserRepository
from src.storage.repositories.audit_log_repository import AuditLogRepository, SQLAlchemyAuditLogRepository
from src.storage.repositories.history_repository import InvoiceHistoryRepository, SQLAlchemyInvoiceHistoryRepository
from src.storage.repositories.processed_message_repository import ProcessedMessageRepository, SQLAlchemyProcessedMessageRepository
from src.storage.repositories.user_config_repository import SQLAlchemyUserConfigRepository, UserConfigRepository


@dataclass(frozen=True)
class StorageDependencies:
    """Готовый набор репозиториев для прикладного слоя."""

    invoice_history: InvoiceHistoryRepository
    processed_messages: ProcessedMessageRepository
    allowed_users: AllowedUserRepository
    user_config: UserConfigRepository
    audit_log: AuditLogRepository


DEFAULT_DB_PATH = Dir.STORAGE_DB


def build_storage_dependencies(
    db_path: Path = DEFAULT_DB_PATH,
) -> StorageDependencies:
    """Инициализирует БД и возвращает репозитории для workflow-композиции."""

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()

    invoice_history = SQLAlchemyInvoiceHistoryRepository(database.session)
    processed_messages = SQLAlchemyProcessedMessageRepository(database.session)
    allowed_users = SQLAlchemyAllowedUserRepository(database.session)
    user_config = SQLAlchemyUserConfigRepository(database.session)
    audit_log = SQLAlchemyAuditLogRepository(database.session)

    return StorageDependencies(
        invoice_history=invoice_history,
        processed_messages=processed_messages,
        allowed_users=allowed_users,
        user_config=user_config,
        audit_log=audit_log,
    )
