from pathlib import Path

import pytest

from src.services.bank.exceptions import BankPdfValidationError
from src.storage.orm import DocumentGenerationHistory
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.system.document_generation_history import DocumentGenerationStatus, DocumentType
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf


def test_fill_bank_confirmation_records_failed_attempt(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    with pytest.raises(BankPdfValidationError, match="Bank confirmation source PDF not found"):
        generate_bank_confirmation(
            telegram_id=123,
            bank_template=tmp_path / "missing.pdf",
            output_dir=tmp_path,
        )

    history_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.BANK_CONFIRMATION, None)
    assert history_entry is not None
    assert history_entry.document_type == DocumentType.BANK_CONFIRMATION
    assert history_entry.document_number is None
    assert history_entry.telegram_id == 123
    assert history_entry.status == DocumentGenerationStatus.FAILED


def test_generate_conversion_order_records_failed_attempt(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    with pytest.raises(ValueError, match="Банковские реквизиты не настроены"):
        generate_conversion_order_pdf(
            telegram_id=123,
            exchange_amount_eur=1500,
            output_dir=tmp_path,
        )

    history_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.CONVERSION_ORDER, "TR-2026-06")
    assert history_entry is not None
    assert history_entry.document_type == DocumentType.CONVERSION_ORDER
    assert history_entry.document_number == "TR-2026-06"
    assert history_entry.telegram_id == 123
    assert history_entry.status == DocumentGenerationStatus.FAILED
