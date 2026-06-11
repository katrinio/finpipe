import pytest

from src.services.bank import bank_fill as fill
from src.storage.orm.database import Database, build_sqlite_url
from src.storage.orm.user.bank_details import BankDetails
from src.utils import Utils
from src.utils.credentials import ENV_PATH_OVERRIDE, EnvVar


def test_build_bank_form_data_reads_bank_details_from_orm(tmp_path, monkeypatch) -> None:
    database = Database(build_sqlite_url(tmp_path / "storage.sqlite3"))
    database.initialize_schema()

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
    monkeypatch.setenv("REGISTRATION_NUMBER", registration_number)
    monkeypatch.setenv("CITY", city)

    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder=recipient,
        account_holder_email="test@example.com",
        account_holder_address="Serbia",
        amount=123.45,
        bank_name="Test Bank",
        account_number=account_number,
        iban="RS123",
        bic="TESTRSBG",
    )

    bank_details = BankDetails.get_by_owner(123)
    assert bank_details is not None

    form_data = fill.build_bank_form_data(5480, "29.05.2026", bank_details)

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
