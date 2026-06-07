from src.storage.database import Database, build_sqlite_url
from src.storage.repositories.sqlalchemy_repositories import (
    SQLAlchemyInvoiceHistoryRepository,
    SQLAlchemyProcessedMessageRepository,
)


def test_invoice_history_repository_crud(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    repository = SQLAlchemyInvoiceHistoryRepository(database.session)

    assert repository.list_invoices() == []
    assert repository.get_last_invoice() is None
    assert repository.invoice_exists("2026-05") is False

    repository.add_invoice("2026-05")
    repository.add_invoice("2026-04")
    repository.add_invoice("2026-05")

    assert repository.invoice_exists("2026-05") is True
    assert repository.list_invoices() == ["2026-04", "2026-05"]
    assert repository.get_last_invoice() == "2026-05"


def test_processed_message_repository_crud_and_replace(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    repository = SQLAlchemyProcessedMessageRepository(database.session)

    assert repository.list_message_ids() == []
    assert repository.is_processed("message-1") is False

    repository.mark_as_processed("message-2")
    repository.mark_as_processed("message-1")
    repository.mark_as_processed("message-2")

    assert repository.is_processed("message-1") is True
    assert repository.list_message_ids() == ["message-1", "message-2"]

    repository.replace_all({"message-9", "message-3"})
    assert repository.list_message_ids() == ["message-3", "message-9"]

    repository.clear()
    assert repository.list_message_ids() == []
