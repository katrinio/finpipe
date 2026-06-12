from pathlib import Path

from src.storage.orm import DocumentGenerationHistory, DocumentGenerationStatus, DocumentType
from src.storage.orm.database import Database, build_sqlite_url


def test_document_generation_history_stores_multiple_attempts_for_same_document(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    DocumentGenerationHistory.add_attempt(
        DocumentType.SALARY_INVOICE, "2026-05", telegram_id=1, status=DocumentGenerationStatus.FAILED, error_message="boom"
    )
    DocumentGenerationHistory.add_attempt(DocumentType.SALARY_INVOICE, "2026-05", telegram_id=1, status=DocumentGenerationStatus.SUCCESS)

    entries = DocumentGenerationHistory.list_by_document(DocumentType.SALARY_INVOICE, "2026-05")

    assert len(entries) == 2
    assert entries[0].document_type == DocumentType.SALARY_INVOICE
    assert entries[0].document_number == "2026-05"
    assert entries[0].status == DocumentGenerationStatus.FAILED
    assert entries[0].error_message == "boom"
    assert entries[1].status == DocumentGenerationStatus.SUCCESS
    assert entries[1].error_message is None


def test_document_generation_history_returns_last_attempt(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    DocumentGenerationHistory.add_attempt(
        DocumentType.SALARY_INVOICE, "2026-05", telegram_id=1, status=DocumentGenerationStatus.FAILED, error_message="boom"
    )
    DocumentGenerationHistory.add_attempt(DocumentType.SALARY_INVOICE, "2026-05", telegram_id=2, status=DocumentGenerationStatus.SUCCESS)

    last_attempt = DocumentGenerationHistory.get_last_attempt(DocumentType.SALARY_INVOICE, "2026-05")

    assert last_attempt is not None
    assert last_attempt.telegram_id == 2
    assert last_attempt.status == DocumentGenerationStatus.SUCCESS


def test_document_generation_history_supports_all_document_types(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    DocumentGenerationHistory.add_attempt(DocumentType.SALARY_INVOICE, "2026-05", telegram_id=1, status=DocumentGenerationStatus.SUCCESS)
    DocumentGenerationHistory.add_attempt(DocumentType.PAYMENT_CONFIRMATION, None, telegram_id=1, status=DocumentGenerationStatus.SUCCESS)
    DocumentGenerationHistory.add_attempt(
        DocumentType.CONVERSION_ORDER, "TR-2026-05", telegram_id=1, status=DocumentGenerationStatus.FAILED, error_message="boom"
    )

    invoice_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.SALARY_INVOICE, "2026-05")
    bank_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.PAYMENT_CONFIRMATION, None)
    transfer_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.CONVERSION_ORDER, "TR-2026-05")

    assert invoice_entry is not None
    assert invoice_entry.document_type == DocumentType.SALARY_INVOICE
    assert bank_entry is not None
    assert bank_entry.document_type == DocumentType.PAYMENT_CONFIRMATION
    assert bank_entry.document_number is None
    assert transfer_entry is not None
    assert transfer_entry.document_type == DocumentType.CONVERSION_ORDER
    assert transfer_entry.document_number == "TR-2026-05"
    assert transfer_entry.status == DocumentGenerationStatus.FAILED
