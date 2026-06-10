from __future__ import annotations

from pathlib import Path

from src.services.profile_template.profile_template_service import ProfileTemplateService
from src.storage.database import Database, build_sqlite_url
from src.storage.orm.bank_details import BankDetails
from src.storage.orm.company_profile import CompanyProfile

PROFILE_YAML = b"""
company_name: Test Company
company_address: Belgrade
account_holder: Test User
account_holder_email: test@example.com
account_holder_address: Serbia
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
"""


def test_profile_import_happy_path_creates_company_profile_and_bank_details(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    profile = ProfileTemplateService.parse(PROFILE_YAML)
    ProfileTemplateService.import_profile(telegram_id=123, profile=profile)

    company_profile = CompanyProfile.get_by_owner(123)
    bank_details = BankDetails.get_by_owner(123)

    assert company_profile is not None
    assert company_profile.company_name == "Test Company"
    assert company_profile.company_address == "Belgrade"

    assert bank_details is not None
    assert bank_details.account_holder == "Test User"
    assert bank_details.account_holder_email == "test@example.com"
    assert bank_details.account_holder_address == "Serbia"
    assert bank_details.bank_name == "Test Bank"
    assert bank_details.account_number == "123"
    assert bank_details.iban == "RS123"
    assert bank_details.bic == "TESTRSBG"


def test_profile_reimport_updates_existing_records(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    first_profile = ProfileTemplateService.parse(PROFILE_YAML)
    ProfileTemplateService.import_profile(telegram_id=123, profile=first_profile)

    second_profile = ProfileTemplateService.parse(
        b"""
company_name: Updated Company
company_address: Novi Sad
account_holder: Updated User
account_holder_email: updated@example.com
account_holder_address: Montenegro
bank_name: Updated Bank
account_number: "999"
iban: RS999
bic: UPDTRSBG
""",
    )
    ProfileTemplateService.import_profile(telegram_id=123, profile=second_profile)

    company_profile = CompanyProfile.get_by_owner(123)
    bank_details = BankDetails.get_by_owner(123)

    assert company_profile is not None
    assert company_profile.company_name == "Updated Company"
    assert company_profile.company_address == "Novi Sad"

    assert bank_details is not None
    assert bank_details.account_holder == "Updated User"
    assert bank_details.account_holder_email == "updated@example.com"
    assert bank_details.account_holder_address == "Montenegro"
    assert bank_details.bank_name == "Updated Bank"
    assert bank_details.account_number == "999"
    assert bank_details.iban == "RS999"
    assert bank_details.bic == "UPDTRSBG"
