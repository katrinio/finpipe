from __future__ import annotations

from pathlib import Path

from src.services.profile_template.profile_template_service import ProfileTemplateService
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils import Utils

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
service_agreement_date: "2026-06-10"
"""


def test_profile_upload_persists_company_profile_and_bank_details(tmp_path: Path) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

    ProfileTemplateService.upload(
        telegram_id=123,
        file_name="profile.yaml",
        file_size=len(PROFILE_YAML),
        file_bytes=PROFILE_YAML,
    )

    company_profile = CompanyProfile.get_by_owner(123)
    bank_details = BankDetails.get_by_owner(123)

    assert company_profile is not None
    assert company_profile.company_name == "Test Company"
    assert company_profile.company_address == "Belgrade"
    assert company_profile.service_agreement_date is not None
    assert company_profile.service_agreement_date.date() == Utils.parse_iso_date("2026-06-10")

    assert bank_details is not None
    assert bank_details.account_holder == "Test User"
    assert bank_details.account_holder_email == "test@example.com"
    assert bank_details.account_holder_address == "Serbia"
    assert bank_details.bank_name == "Test Bank"
    assert bank_details.account_number == "123"
    assert bank_details.iban == "RS123"
    assert bank_details.bic == "TESTRSBG"
