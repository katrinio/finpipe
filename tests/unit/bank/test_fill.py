import pytest

from src.services.bank import fill


def test_build_bank_form_data_reads_required_env(monkeypatch) -> None:
    monkeypatch.setenv("PAYMENT_NUMBER", "1")
    monkeypatch.setenv("PAYMENT_CODE", "303")
    monkeypatch.setenv("PAYMENT_DESCRIPTION", "performance of duties")
    monkeypatch.setenv("RECIPIENT", "KATRIN TORSUNOVA PR")
    monkeypatch.setenv("REGISTRATION_NUMBER", "68006848")
    monkeypatch.setenv("ACCOUNT_NUMBER", "190-0000000128270-73")
    monkeypatch.setenv("CITY", "Beograd")

    form_data = fill.build_bank_form_data(2180, "29.05.2026")

    assert form_data == {
        "number": "1",
        "code": "303",
        "year": "2026",
        "description": "performance of duties",
        "recipient": "KATRIN TORSUNOVA PR",
        "registration_number": "68006848",
        "account_number": "190-0000000128270-73",
        "amount": "2180.00 \u20ac",
        "place_and_date": "Beograd 29.05.2026",
    }


def test_get_required_env_raises_for_missing_value(monkeypatch) -> None:
    monkeypatch.delenv("PAYMENT_NUMBER", raising=False)

    with pytest.raises(RuntimeError, match="PAYMENT_NUMBER"):
        fill.get_required_env("PAYMENT_NUMBER")
