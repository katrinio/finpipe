import json

from sqlalchemy import select

from src.storage.database import Database, build_sqlite_url
from src.storage.migration import JsonToSQLiteMigrator
from src.storage.orm import AppliedMigration
from src.storage.sqlalchemy_repositories import (
    SQLAlchemyInvoiceHistoryRepository,
    SQLAlchemyProcessedMessageRepository,
)


def test_json_to_sqlite_migration_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "storage.sqlite3"
    history_path = tmp_path / "history.json"
    processed_messages_path = tmp_path / "processed_messages.json"

    history_path.write_text(
        json.dumps({"invoices": ["2026-05", "2026-04", "2026-05"]}),
        encoding="utf-8",
    )
    processed_messages_path.write_text(
        json.dumps({"processed_messages": ["msg-2", "msg-1", "msg-2"]}),
        encoding="utf-8",
    )

    database = Database(build_sqlite_url(db_path))
    database.initialize_schema()
    invoice_repository = SQLAlchemyInvoiceHistoryRepository(database.session)
    processed_repository = SQLAlchemyProcessedMessageRepository(database.session)
    migrator = JsonToSQLiteMigrator(
        database=database,
        invoice_history_path=history_path,
        processed_messages_path=processed_messages_path,
        invoice_repository=invoice_repository,
        processed_message_repository=processed_repository,
    )

    migrator.migrate()
    migrator.migrate()

    assert invoice_repository.list_invoices() == ["2026-04", "2026-05"]
    assert processed_repository.list_message_ids() == ["msg-1", "msg-2"]

    with database.session() as session:
        migrations = session.scalars(select(AppliedMigration.migration_name).order_by(AppliedMigration.migration_name)).all()

    assert migrations == [
        "legacy_history_json_to_sqlite",
        "legacy_processed_messages_json_to_sqlite",
    ]
