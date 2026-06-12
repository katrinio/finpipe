from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from src.constants import TestData
from src.storage.orm import DocumentGenerationHistory, DocumentGenerationStatus, DocumentType, UserConfig
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.workflows.tasks.generate_invoice import generate_invoice_pdf


def test_generate_invoice_pdf_uses_user_config_invoice_amount(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    UserConfig.upsert(telegram_id=123, invoice_amount=1500)
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_email="john@example.com",
        account_holder_address="Amsterdam",
        amount=1500,
        bank_name="ABN AMRO",
        account_number="123456789",
        iban="NL91ABNA0417164300",
        bic="ABNANL2A",
    )
    output_path = generate_invoice_pdf(
        telegram_id=123,
        invoice_date=date(2026, 5, 20),
        template_path=TestData.INVOICE_TEMPLATE_PATH,
        output_dir=tmp_path,
    )

    assert output_path.exists()
    assert output_path.name.startswith("invoice-")
    history_entry = DocumentGenerationHistory.get_last_attempt(DocumentType.SALARY_INVOICE, output_path.stem.removeprefix("invoice-"))
    assert history_entry is not None
    assert history_entry.document_type == DocumentType.SALARY_INVOICE
    assert history_entry.document_number == "2026-05"
    assert history_entry.telegram_id == 123
    assert history_entry.status == DocumentGenerationStatus.SUCCESS
    assert history_entry.error_message is None


def test_generate_invoice_pdf_fails_when_invoice_amount_is_missing(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_email="john@example.com",
        account_holder_address="Amsterdam",
        amount=1500,
        bank_name="ABN AMRO",
        account_number="123456789",
        iban="NL91ABNA0417164300",
        bic="ABNANL2A",
    )
    with pytest.raises(ValueError, match="Сумма Invoice не указана"):
        generate_invoice_pdf(
            telegram_id=123,
            invoice_date=date(2026, 5, 20),
            template_path=TestData.INVOICE_TEMPLATE_PATH,
            output_dir=tmp_path,
        )

    failed_entries = DocumentGenerationHistory.list_by_document(DocumentType.SALARY_INVOICE, "2026-05")
    assert len(failed_entries) == 1
    assert failed_entries[0].document_type == DocumentType.SALARY_INVOICE
    assert failed_entries[0].document_number == "2026-05"
    assert failed_entries[0].telegram_id == 123
    assert failed_entries[0].status == DocumentGenerationStatus.FAILED
    assert failed_entries[0].error_message == "Сумма Invoice не указана. Используйте «💰 Указать сумму»."


def test_generate_invoice_pdf_allows_regeneration_for_same_invoice_number(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()
    UserConfig.upsert(telegram_id=123, invoice_amount=1500)
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_email="john@example.com",
        account_holder_address="Amsterdam",
        amount=1500,
        bank_name="ABN AMRO",
        account_number="123456789",
        iban="NL91ABNA0417164300",
        bic="ABNANL2A",
    )

    first_output = generate_invoice_pdf(
        telegram_id=123,
        invoice_date=date(2026, 5, 20),
        template_path=TestData.INVOICE_TEMPLATE_PATH,
        output_dir=tmp_path,
    )
    second_output = generate_invoice_pdf(
        telegram_id=123,
        invoice_date=date(2026, 5, 20),
        template_path=TestData.INVOICE_TEMPLATE_PATH,
        output_dir=tmp_path,
    )

    assert first_output == second_output
    entries = DocumentGenerationHistory.list_by_document(DocumentType.SALARY_INVOICE, first_output.stem.removeprefix("invoice-"))
    assert len(entries) == 2
    assert entries[0].status == DocumentGenerationStatus.SUCCESS
    assert entries[1].status == DocumentGenerationStatus.SUCCESS
    last_attempt = DocumentGenerationHistory.get_last_attempt(DocumentType.SALARY_INVOICE, first_output.stem.removeprefix("invoice-"))
    assert last_attempt is not None
    assert last_attempt.id == entries[-1].id
