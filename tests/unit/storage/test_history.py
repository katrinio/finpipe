from pathlib import Path

import pytest
from sqlalchemy import select

from src.storage.database import Database, build_sqlite_url
from src.storage.history import HistoryStorage
from src.storage.orm import HistoryRecord


def test_history_storage_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage_file = tmp_path / "history.json"
    database_path = tmp_path / "storage.sqlite3"

    monkeypatch.setattr(HistoryStorage, "FILE_PATH", storage_file)
    monkeypatch.setattr(HistoryStorage, "DB_PATH", database_path)

    assert HistoryStorage.load_history() == set()
    assert HistoryStorage.invoice_exists("2026-05") is False
    assert HistoryStorage.get_last_invoice() is None

    HistoryStorage.add_invoice("2026-05")
    HistoryStorage.add_invoice("2026-04")
    HistoryStorage.add_invoice("2026-05")

    assert HistoryStorage.invoice_exists("2026-05") is True
    assert HistoryStorage.list_invoices() == ["2026-04", "2026-05"]
    assert HistoryStorage.get_last_invoice() == "2026-05"

    database = Database(build_sqlite_url(database_path))
    with database.session() as session:
        rows = session.scalars(select(HistoryRecord.invoice_number).order_by(HistoryRecord.invoice_number)).all()

    assert rows == ["2026-04", "2026-05"]
