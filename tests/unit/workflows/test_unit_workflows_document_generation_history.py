from __future__ import annotations

from pathlib import Path

import pytest

from src.storage.orm import DocumentGenerationHistory, DocumentGenerationStatus, DocumentType
from src.storage.orm.database import Database, build_sqlite_url
from src.workflows.tasks.fill_bank_pdf import fill_bank_pdf_with_data
from src.workflows.tasks.generate_transfer_request import generate_transfer_request_pdf


def test_fill_bank_pdf_records_failed_bank_pdf_attempt(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    with pytest.raises(FileNotFoundError):
        fill_bank_pdf_with_data(
            telegram_id=123,
            bank_template=tmp_path / "missing.pdf",
            output_dir=tmp_path,
        )

    history_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.BANK_PDF, None)
    assert history_entry is not None
    assert history_entry.document_type == DocumentType.BANK_PDF
    assert history_entry.document_number is None
    assert history_entry.telegram_id == 123
    assert history_entry.status == DocumentGenerationStatus.FAILED


def test_generate_transfer_request_records_failed_transfer_request_attempt(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    with pytest.raises(ValueError, match="Банковские реквизиты не настроены"):
        generate_transfer_request_pdf(
            telegram_id=123,
            amount="1500",
            output_dir=tmp_path,
        )

    history_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.TRANSFER_REQUEST, "TR-2026-06")
    assert history_entry is not None
    assert history_entry.document_type == DocumentType.TRANSFER_REQUEST
    assert history_entry.document_number == "TR-2026-06"
    assert history_entry.telegram_id == 123
    assert history_entry.status == DocumentGenerationStatus.FAILED
