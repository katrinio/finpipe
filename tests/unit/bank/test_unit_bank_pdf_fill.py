import pytest

from src.services.bank import bank_fill as fill
from src.utils import Utils
from src.utils.credentials import ENV_PATH_OVERRIDE, EnvVar


def test_build_bank_form_data_reads_required_env(monkeypatch) -> None:
    payment_number = Utils.generate_int_string(2)
    payment_code = Utils.generate_int_string(3)
    payment_description = Utils.generate_random_sentence()
    recipient = Utils.generate_name()
    registration_number = Utils.generate_int_string()
    account_number = Utils.generate_int_string(2)
    city = Utils.generate_city()

    monkeypatch.setenv("PAYMENT_NUMBER", payment_number)
    monkeypatch.setenv("PAYMENT_CODE", payment_code)
    monkeypatch.setenv("PAYMENT_DESCRIPTION", payment_description)
    monkeypatch.setenv("ACCOUNT_HOLDER", recipient)
    monkeypatch.setenv("REGISTRATION_NUMBER", registration_number)
    monkeypatch.setenv("ACCOUNT_NUMBER", account_number)
    monkeypatch.setenv("CITY", city)

    form_data = fill.build_bank_form_data(5480, "29.05.2026")

    assert form_data == {
        "number": payment_number,
        "code": payment_code,
        "year": "2026",
        "description": payment_description,
        "recipient": recipient,
        "registration_number": registration_number,
        "account_number": account_number,
        "amount": "5480.00 \u20ac",
        "place_and_date": f"{city} 29.05.2026",
    }


def test_get_required_env_raises_for_missing_value(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(tmp_path / "missing.env"))
    monkeypatch.delenv("PAYMENT_NUMBER", raising=False)
    EnvVar.reset_dotenv_cache()

    with pytest.raises(RuntimeError, match="PAYMENT_NUMBER"):
        fill.get_required_env("PAYMENT_NUMBER")
