from pathlib import Path

from src.integrations.telegram.handlers.profile_handlers import ProfileHandlers
from src.integrations.telegram.state_service import UserStateService
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from tests.fakes.fake_telegram import FakeTelegramClient


def test_profile_upload_returns_success_message_with_real_values(tmp_path: Path) -> None:
    build_storage_dependencies(tmp_path / "storage.sqlite3")
    telegram_client = FakeTelegramClient()
    handlers = ProfileHandlers(telegram_client, state_service=UserStateService)

    handlers.handle_profile_template_upload(
        telegram_id=123,
        file_name="profile.yaml",
        file_size=len(
            b"""
company_name: Test Company
company_address: Belgrade
account_holder: Test User
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
        ),
        file_bytes=b"""
company_name: Test Company
company_address: Belgrade
account_holder: Test User
bank_name: Test Bank
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
    )

    assert telegram_client.sent_messages == [
        "✅ Профиль успешно загружен.\nКомпания: Test Company\nБанк: Test Bank",
    ]
    assert CompanyProfile.get_by_owner(123) is not None
    assert BankDetails.get_by_owner(123) is not None


def test_profile_upload_rejects_incomplete_profile_without_persisting_data(tmp_path: Path) -> None:
    build_storage_dependencies(tmp_path / "storage.sqlite3")
    telegram_client = FakeTelegramClient()
    handlers = ProfileHandlers(telegram_client, state_service=UserStateService)

    handlers.handle_profile_template_upload(
        telegram_id=123,
        file_name="profile.yaml",
        file_size=len(
            b"""
company_name: ""
company_address: Belgrade
account_holder: Test User
bank_name: ""
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
        ),
        file_bytes=b"""
company_name: ""
company_address: Belgrade
account_holder: Test User
bank_name: ""
account_number: "123"
iban: RS123
bic: TESTRSBG
""",
    )

    assert telegram_client.sent_messages == [
        "❌ Профиль заполнен не полностью.\nНе заполнены обязательные поля:\n• company_name\n• bank_name\nИсправьте шаблон и загрузите его повторно.",
    ]
    assert CompanyProfile.get_by_owner(123) is None
    assert BankDetails.get_by_owner(123) is None
