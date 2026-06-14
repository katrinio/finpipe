from pathlib import Path

import pytest

from src.services.profile_template.exceptions import InvalidProfileTemplateError
from src.services.profile_template.profile_template_service import ProfileTemplateService
from src.storage.orm.database import Database
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils import Utils
from tests.helpers.database import build_test_database_url, initialize_test_database

PROFILE_YAML = b"""
company_name: Test Company
company_address: Belgrade
registration_number: "12345678"
city: Belgrade
account_holder: Test User
account_holder_email: test@example.com
account_holder_address: Serbia
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
service_agreement_date: "2026-06-10"
payment_number: "42"
payment_code: "63"
payment_description: Salary payment
"""


def test_profile_upload_persists_company_profile_and_bank_details(tmp_path: Path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

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
    assert company_profile.registration_number == "12345678"
    assert company_profile.city == "Belgrade"
    assert company_profile.service_agreement_date is not None
    assert company_profile.service_agreement_date.date() == Utils.parse_iso_date("2026-06-10")
    assert company_profile.payment_number == "42"
    assert company_profile.payment_code == "63"
    assert company_profile.payment_description == "Salary payment"

    assert bank_details is not None
    assert bank_details.account_holder == "Test User"
    assert bank_details.account_holder_email == "test@example.com"
    assert bank_details.account_holder_address == "Serbia"
    assert bank_details.bank_name == "Test Bank"
    assert bank_details.account_number == "123"
    assert bank_details.iban == "RS123"
    assert bank_details.bic == "TESTRSBG"


@pytest.mark.parametrize(
    ("file_bytes", "missing_fields"),
    [
        (
            b"""
company_name: Test Company
company_address: Belgrade
account_holder: Test User
bank_name: Test Bank
account_number: "123"
bic: TESTRSBG
""",
            ["iban"],
        ),
        (
            b"""
company_name: ""
company_address: Belgrade
account_holder: Test User
bank_name: ""
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
            ["company_name", "bank_name"],
        ),
    ],
)
def test_profile_upload_rejects_incomplete_profile_without_persisting_data(
    tmp_path: Path,
    file_bytes: bytes,
    missing_fields: list[str],
) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    with pytest.raises(InvalidProfileTemplateError) as exc_info:
        ProfileTemplateService.upload(
            telegram_id=123,
            file_name="profile.yaml",
            file_size=len(file_bytes),
            file_bytes=file_bytes,
        )

    message = str(exc_info.value)
    for field_name in missing_fields:
        assert f"• {field_name}" in message

    assert CompanyProfile.get_by_owner(123) is None
    assert BankDetails.get_by_owner(123) is None
