import json
from pathlib import Path

import pytest

from src.storage.history import HistoryStorage


def test_history_storage_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage_file = tmp_path / "history.json"
    monkeypatch.setattr(HistoryStorage, "FILE_PATH", storage_file)

    assert HistoryStorage.load_history() == set()
    assert HistoryStorage.invoice_exists("2026-05") is False
    assert HistoryStorage.get_last_invoice() is None

    HistoryStorage.add_invoice("2026-05")
    HistoryStorage.add_invoice("2026-04")
    HistoryStorage.add_invoice("2026-05")

    assert HistoryStorage.invoice_exists("2026-05") is True
    assert HistoryStorage.list_invoices() == ["2026-04", "2026-05"]
    assert HistoryStorage.get_last_invoice() == "2026-05"
    assert json.loads(storage_file.read_text(encoding="utf-8")) == {
        "invoices": [
            "2026-04",
            "2026-05",
        ],
    }
