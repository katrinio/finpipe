from src.services.bank import bank_confirmation as fill
from src.storage.orm.database import Database
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils import Utils
from tests.helpers.database import build_test_database_url, initialize_test_database


def test_build_bank_form_data_reads_bank_details_from_orm(tmp_path) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)

    payment_number = Utils.generate_int_string(2)
    payment_code = Utils.generate_int_string(3)
    payment_description = Utils.generate_random_sentence()
    recipient = Utils.generate_name()
    registration_number = Utils.generate_int_string()
    account_number = Utils.generate_int_string(2)
    city = Utils.generate_city()

    CompanyProfile.upsert(
        owner_telegram_id=123,
        company_name="Test Company",
        company_address="Belgrade",
        registration_number=registration_number,
        city=city,
        payment_number=payment_number,
        payment_code=payment_code,
        payment_description=payment_description,
    )
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder=recipient,
        account_holder_address="Serbia",
        amount=123.45,
        bank_name="Test Bank",
        account_number=account_number,
        iban="RS123",
        bic="TESTRSBG",
    )

    bank_details = BankDetails.get_by_owner(123)
    company_profile = CompanyProfile.get_by_owner(123)
    assert bank_details is not None
    assert company_profile is not None

    form_data = fill.build_bank_form_data(5480, "29.05.2026", company_profile, bank_details)

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
