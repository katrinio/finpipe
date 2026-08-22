from datetime import datetime
from pathlib import Path

from src.storage.orm.database import Database
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_company_profile_upsert_creates_and_updates_without_overwriting_with_none(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Test Company",
        company_address="Belgrade",
        service_agreement_date=datetime(2026, 6, 10),
    )

    created = CompanyProfile.get_by_owner(123)
    assert created is not None
    created_id = created.id

    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name=None,
        company_address="Novi Sad",
        service_agreement_date=None,
    )

    updated = CompanyProfile.get_by_owner(123)
    assert updated is not None
    assert updated.id == created_id
    assert updated.company_name == "Test Company"
    assert updated.company_address == "Novi Sad"
    assert updated.service_agreement_date == datetime(2026, 6, 10)


def test_bank_details_upsert_creates_and_updates_without_overwriting_with_none(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="Test User",
        account_holder_address="Serbia",
        bank_name="Test Bank",
        account_number="123",
        iban="RS123",
        bic="TESTRSBG",
    )

    created = BankDetails.get_by_owner(123)
    assert created is not None
    created_id = created.id

    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder=None,
        account_holder_address="Montenegro",
        bank_name="Updated Bank",
        account_number=None,
        iban="RS999",
        bic=None,
    )

    updated = BankDetails.get_by_owner(123)
    assert updated is not None
    assert updated.id == created_id
    assert updated.account_holder == "Test User"
    assert updated.account_holder_address == "Montenegro"
    assert updated.bank_name == "Updated Bank"
    assert updated.account_number == "123"
    assert updated.iban == "RS999"
    assert updated.bic == "TESTRSBG"
