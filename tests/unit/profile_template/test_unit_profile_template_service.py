from __future__ import annotations

from src.services.profile_template.profile_template_service import ProfileTemplateService


def test_parse_converts_yaml_to_profile_template() -> None:
    profile = ProfileTemplateService.parse(
        b"""
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
""",
    )

    assert profile.company_name == "Test Company"
    assert profile.company_address == "Belgrade"
    assert profile.account_holder == "Test User"
    assert profile.account_holder_email == "test@example.com"
    assert profile.account_holder_address == "Serbia"
    assert profile.bank_name == "Test Bank"
    assert profile.account_number == "123"
    assert profile.iban == "RS123"
    assert profile.bic == "TESTRSBG"
    assert profile.service_agreement_date == "2026-06-10"


def test_parse_turns_missing_values_into_none() -> None:
    profile = ProfileTemplateService.parse(
        b"""
company_name: Test Company
bank_name: Test Bank
""",
    )

    assert profile.company_name == "Test Company"
    assert profile.company_address is None
    assert profile.account_holder is None
    assert profile.account_holder_email is None
    assert profile.account_holder_address is None
    assert profile.bank_name == "Test Bank"
    assert profile.account_number is None
    assert profile.iban is None
    assert profile.bic is None
    assert profile.service_agreement_date is None
