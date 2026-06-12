from pathlib import Path

from src.storage.orm import HistoryRecord, InvoiceGenerationStatus
from src.storage.orm.database import Database, build_sqlite_url


def test_history_record_stores_multiple_attempts_for_same_invoice_number(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    HistoryRecord.add_attempt("2026-05", telegram_id=1, status=InvoiceGenerationStatus.FAILED, error_message="boom")
    HistoryRecord.add_attempt("2026-05", telegram_id=1, status=InvoiceGenerationStatus.SUCCESS)

    entries = HistoryRecord.list_by_invoice_number("2026-05")

    assert len(entries) == 2
    assert entries[0].status == InvoiceGenerationStatus.FAILED
    assert entries[0].error_message == "boom"
    assert entries[1].status == InvoiceGenerationStatus.SUCCESS
    assert entries[1].error_message is None


def test_history_record_returns_last_attempt(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    HistoryRecord.add_attempt("2026-05", telegram_id=1, status=InvoiceGenerationStatus.FAILED, error_message="boom")
    HistoryRecord.add_attempt("2026-05", telegram_id=2, status=InvoiceGenerationStatus.SUCCESS)

    last_attempt = HistoryRecord.get_last_attempt("2026-05")

    assert last_attempt is not None
    assert last_attempt.telegram_id == 2
    assert last_attempt.status == InvoiceGenerationStatus.SUCCESS
