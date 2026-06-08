from src.storage.database import Database, build_sqlite_url
from src.storage.orm import HistoryRecord, ProcessedMessage


def test_invoice_history_repository_crud(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    assert HistoryRecord.list_invoices() == []
    assert HistoryRecord.get_last_invoice() is None
    assert HistoryRecord.invoice_exists("2026-05") is False

    HistoryRecord.add_invoice("2026-05")
    HistoryRecord.add_invoice("2026-04")
    HistoryRecord.add_invoice("2026-05")

    assert HistoryRecord.invoice_exists("2026-05") is True
    assert HistoryRecord.list_invoices() == ["2026-04", "2026-05"]
    assert HistoryRecord.get_last_invoice() == "2026-05"


def test_processed_message_repository_crud_and_replace(tmp_path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    assert ProcessedMessage.list_message_ids() == []
    assert ProcessedMessage.is_processed("message-1") is False

    ProcessedMessage.mark_as_processed("message-2")
    ProcessedMessage.mark_as_processed("message-1")
    ProcessedMessage.mark_as_processed("message-2")

    assert ProcessedMessage.is_processed("message-1") is True
    assert ProcessedMessage.list_message_ids() == ["message-1", "message-2"]

    ProcessedMessage.replace_all({"message-9", "message-3"})
    assert ProcessedMessage.list_message_ids() == ["message-3", "message-9"]

    ProcessedMessage.clear_processed_message()
    assert ProcessedMessage.list_message_ids() == []
