from datetime import date, datetime
from pathlib import Path

import pytest

from src.constants import TestData
from src.services.invoice.exceptions import InvoiceGenerationError
from src.storage.orm import UserConfig
from src.storage.orm.database import Database
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.workflows.tasks.generate_invoice import generate_invoice_pdf
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_generate_invoice_pdf_uses_user_config_invoice_amount(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    UserConfig.upsert(telegram_id=123, invoice_amount_eur=1500)
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_address="Amsterdam",
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


def test_generate_invoice_pdf_fails_when_invoice_amount_is_missing(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_address="Amsterdam",
        bank_name="ABN AMRO",
        account_number="123456789",
        iban="NL91ABNA0417164300",
        bic="ABNANL2A",
    )
    with pytest.raises(InvoiceGenerationError, match="Сумма Salary Invoice не указана"):
        generate_invoice_pdf(
            telegram_id=123,
            invoice_date=date(2026, 5, 20),
            template_path=TestData.INVOICE_TEMPLATE_PATH,
            output_dir=tmp_path,
        )


def test_generate_invoice_pdf_allows_regeneration_for_same_invoice_number(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    UserConfig.upsert(telegram_id=123, invoice_amount_eur=1500)
    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Acme Ltd",
        company_address="Belgrade",
        service_agreement_date=datetime(2025, 6, 10),
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="John Doe",
        account_holder_address="Amsterdam",
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
