"""Миграция данных из legacy JSON-файлов в SQLite."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.storage.database import Database
from src.storage.orm import AppliedMigration
from src.storage.repositories import InvoiceHistoryRepository, ProcessedMessageRepository

LOGGER = logging.getLogger(__name__)
INVOICE_HISTORY_MIGRATION = "legacy_history_json_to_sqlite"
PROCESSED_MESSAGES_MIGRATION = "legacy_processed_messages_json_to_sqlite"


class JsonToSQLiteMigrator:
    """Одноразово переносит legacy JSON-данные в таблицы SQLite."""

    def __init__(
        self,
        database: Database,
        invoice_history_path: Path,
        processed_messages_path: Path,
        invoice_repository: InvoiceHistoryRepository,
        processed_message_repository: ProcessedMessageRepository,
    ) -> None:
        self._database = database
        self._invoice_history_path = invoice_history_path
        self._processed_messages_path = processed_messages_path
        self._invoice_repository = invoice_repository
        self._processed_message_repository = processed_message_repository

    def migrate(self) -> None:
        """Выполняет безопасную и идемпотентную миграцию обоих JSON-хранилищ."""

        self._migrate_invoice_history()
        self._migrate_processed_messages()

    def _migrate_invoice_history(self) -> None:
        if self._has_migration(INVOICE_HISTORY_MIGRATION):
            return

        invoice_numbers = self._load_json_array(self._invoice_history_path, "invoices")
        if invoice_numbers:
            LOGGER.info(
                "Migrating %s invoice history records from %s",
                len(invoice_numbers),
                self._invoice_history_path,
            )
            for invoice_number in invoice_numbers:
                self._invoice_repository.add_invoice(invoice_number)
        else:
            LOGGER.info("No invoice history JSON data found for migration at %s", self._invoice_history_path)

        self._mark_migration_applied(INVOICE_HISTORY_MIGRATION)

    def _migrate_processed_messages(self) -> None:
        if self._has_migration(PROCESSED_MESSAGES_MIGRATION):
            return

        message_ids = self._load_json_array(self._processed_messages_path, "processed_messages")
        if message_ids:
            LOGGER.info(
                "Migrating %s processed message records from %s",
                len(message_ids),
                self._processed_messages_path,
            )
            for message_id in message_ids:
                self._processed_message_repository.mark_as_processed(message_id)
        else:
            LOGGER.info("No processed messages JSON data found for migration at %s", self._processed_messages_path)

        self._mark_migration_applied(PROCESSED_MESSAGES_MIGRATION)

    def _load_json_array(self, file_path: Path, key: str) -> list[str]:
        if not file_path.exists():
            return []

        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)

        values = data.get(key, [])
        return sorted({str(value) for value in values})

    def _has_migration(self, migration_name: str) -> bool:
        with self._database.session() as session:
            statement = (
                select(AppliedMigration.migration_name)
                .where(
                    AppliedMigration.migration_name == migration_name,
                )
                .limit(1)
            )
            return session.scalar(statement) is not None

    def _mark_migration_applied(self, migration_name: str) -> None:
        with self._database.session() as session:
            session.add(AppliedMigration(migration_name=migration_name))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
        LOGGER.info("Applied migration %s", migration_name)
