from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.constants import TestData
from src.services.invoice.exceptions import InvoiceGenerationError
from src.storage.orm import UserConfig
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
    output_path = generate_invoice_pdf(telegram_id=123, template_path=TestData.INVOICE_TEMPLATE_PATH, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.name.startswith("invoice-")


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
    with pytest.raises(InvoiceGenerationError, match="Сумма Invoice не указана"):
        generate_invoice_pdf(telegram_id=123, template_path=TestData.INVOICE_TEMPLATE_PATH, output_dir=tmp_path)
