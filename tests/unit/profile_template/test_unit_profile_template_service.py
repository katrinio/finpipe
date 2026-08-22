import pytest

from src.services.profile_template.exceptions import InvalidProfileTemplateError
from src.services.profile_template.profile_template_service import ProfileTemplateService


def test_parse_converts_yaml_to_profile_template() -> None:
    profile = ProfileTemplateService.parse(
        b"""
company_name: Test Company
company_address: Belgrade
registration_number: 12345678
city: Belgrade
account_holder: Test User
account_holder_address: Serbia
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
service_agreement_date: "2026-06-10"
payment_number: "1"
payment_code: "2"
payment_description: Fee
""",
    )

    assert profile.company_name == "Test Company"
    assert profile.company_address == "Belgrade"
    assert profile.registration_number == "12345678"
    assert profile.city == "Belgrade"
    assert profile.account_holder == "Test User"
    assert profile.account_holder_address == "Serbia"
    assert profile.bank_name == "Test Bank"
    assert profile.account_number == "123"
    assert profile.iban == "RS123"
    assert profile.bic == "TESTRSBG"
    assert profile.service_agreement_date == "2026-06-10"
    assert profile.payment_number == "1"
    assert profile.payment_code == "2"
    assert profile.payment_description == "Fee"


def test_parse_turns_missing_values_into_none() -> None:
    profile = ProfileTemplateService.parse(
        b"""
company_name: Test Company
bank_name: Test Bank
""",
    )

    assert profile.company_name == "Test Company"
    assert profile.company_address is None
    assert profile.registration_number is None
    assert profile.city is None
    assert profile.account_holder is None
    assert profile.account_holder_address is None
    assert profile.bank_name == "Test Bank"
    assert profile.account_number is None
    assert profile.iban is None
    assert profile.bic is None
    assert profile.service_agreement_date is None
    assert profile.payment_number is None
    assert profile.payment_code is None
    assert profile.payment_description is None


def test_validate_required_fields_accepts_complete_profile() -> None:
    profile = ProfileTemplateService.parse(
        b"""
company_name: Test Company
company_address: Belgrade
account_holder: Test User
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
    )

    ProfileTemplateService.validate_required_fields(profile)


@pytest.mark.parametrize(
    ("yaml_bytes", "expected_fields"),
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
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
            ["company_name"],
        ),
        (
            b"""
company_name: "   "
company_address: ""
account_holder: Test User
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
            ["company_name", "company_address"],
        ),
    ],
)
def test_validate_required_fields_rejects_missing_values(yaml_bytes: bytes, expected_fields: list[str]) -> None:
    profile = ProfileTemplateService.parse(yaml_bytes)

    with pytest.raises(InvalidProfileTemplateError) as exc_info:
        ProfileTemplateService.validate_required_fields(profile)

    for field_name in expected_fields:
        assert f"• {field_name}" in str(exc_info.value)
