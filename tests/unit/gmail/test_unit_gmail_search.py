from datetime import date

import pytest

from src.integrations.gmail import search
from src.storage.orm.database import Database
from src.storage.orm.user.bank_details import BankDetails
from src.utils.credentials import ENV_PATH_OVERRIDE, EnvVar
from tests.helpers.database import build_test_database_url, initialize_test_database


class FakeMessagesApi:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.list_kwargs = None

    def list(self, **kwargs):
        self.list_kwargs = kwargs
        return self

    def execute(self) -> dict:
        return self.response


class FakeUsersApi:
    def __init__(self, messages_api: FakeMessagesApi) -> None:
        self.messages_api = messages_api

    def messages(self) -> FakeMessagesApi:
        return self.messages_api


class FakeGmailService:
    def __init__(self, response: dict) -> None:
        self.messages_api = FakeMessagesApi(response)

    def users(self) -> FakeUsersApi:
        return FakeUsersApi(self.messages_api)


def test_load_bank_email_search_config_prefers_profile_over_env(tmp_path, monkeypatch) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="Test User",
        bank_name="Test Bank",
        account_number="123",
        iban="RS123",
        bic="TESTRSBG",
        bank_confirmation_email_sender="bank@profile.rs",
        bank_confirmation_email_recipient="company@profile.rs",
        bank_confirmation_email_subject_contains="profile subject",
    )

    monkeypatch.setenv("BANK_EMAIL_FROM", "bank@env.rs")
    monkeypatch.setenv("BANK_EMAIL_TO", "company@env.rs")
    monkeypatch.setenv("BANK_EMAIL_SUBJECT", "env subject")
    EnvVar.reset_dotenv_cache()

    config = search.load_bank_email_search_config(123)

    assert config.source == "profile"
    assert config.sender == "bank@profile.rs"
    assert config.recipient == "company@profile.rs"
    assert config.subject_contains == "profile subject"


def test_load_bank_email_search_config_uses_env_fallback_when_profile_is_empty(tmp_path, monkeypatch) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    BankDetails.upsert(
        owner_telegram_id=123,
        account_holder="Test User",
        bank_name="Test Bank",
        account_number="123",
        iban="RS123",
        bic="TESTRSBG",
    )

    monkeypatch.setenv("BANK_EMAIL_FROM", "bank@env.rs")
    monkeypatch.setenv("BANK_EMAIL_TO", "company@env.rs")
    monkeypatch.setenv("BANK_EMAIL_SUBJECT", "env subject")
    EnvVar.reset_dotenv_cache()

    config = search.load_bank_email_search_config(None)

    assert config.source == "env"
    assert config.sender == "bank@env.rs"
    assert config.recipient == "company@env.rs"
    assert config.subject_contains == "env subject"


def test_load_bank_email_search_config_requires_settings(tmp_path, monkeypatch) -> None:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(tmp_path / "missing.env"))
    monkeypatch.delenv("BANK_EMAIL_FROM", raising=False)
    monkeypatch.delenv("BANK_EMAIL_TO", raising=False)
    monkeypatch.delenv("BANK_EMAIL_SUBJECT", raising=False)
    EnvVar.reset_dotenv_cache()

    with pytest.raises(RuntimeError, match="bank_confirmation_email"):
        search.load_bank_email_search_config(None)


def test_build_bank_email_query_uses_filters() -> None:
    config = search.BankEmailSearchConfig(
        sender='bank"sender@example.com',
        recipient='company"recipient@example.com',
        subject_contains='KATRIN "TORSUNOVA" PR',
        source="profile",
    )

    query = search.build_bank_email_query(config)

    today = date.today()
    month_start = f"{today.year}/{today.month:02d}/01"
    assert query == (
        f'subject:"KATRIN \\"TORSUNOVA\\" PR" '
        f'from:"bank\\"sender@example.com" '
        f'to:"company\\"recipient@example.com" after:{month_start} has:attachment'
    )


def test_build_bank_email_result_maps_headers() -> None:
    bank_email = search.build_bank_email_result(
        {
            "id": "message-123",
            "threadId": "thread-456",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Bank payment"},
                    {"name": "From", "value": "bank@example.com"},
                    {"name": "Date", "value": "Fri, 29 May 2026"},
                ],
            },
        }
    )

    assert bank_email.subject == "Bank payment"
    assert bank_email.sender == "bank@example.com"
    assert bank_email.date == "Fri, 29 May 2026"
    assert bank_email.message_id == "message-123"
    assert bank_email.thread_id == "thread-456"


def test_find_bank_email_returns_none_when_no_messages(monkeypatch) -> None:
    monkeypatch.setattr(
        search,
        "load_bank_email_search_config",
        lambda _owner_telegram_id=None: search.BankEmailSearchConfig(
            sender="bank@example.com",
            recipient="company@example.com",
            subject_contains="payment",
            source="profile",
        ),
    )
    service = FakeGmailService({"messages": []})

    assert search.find_bank_email(service) is None
    assert service.messages_api.list_kwargs == {
        "userId": "me",
        "q": f'subject:"payment" '
        f'from:"bank@example.com" '
        f'to:"company@example.com" '
        f"after:{date.today().year}/{date.today().month:02d}/01 "
        f"has:attachment",
        "maxResults": 10,
    }


def test_find_bank_email_selects_newest_message(monkeypatch) -> None:
    monkeypatch.setattr(
        search,
        "load_bank_email_search_config",
        lambda _owner_telegram_id=None: search.BankEmailSearchConfig(
            sender="bank@example.com",
            recipient="company@example.com",
            subject_contains="payment",
            source="profile",
        ),
    )

    metadata_by_id = {
        "old": {
            "id": "old",
            "threadId": "thread-old",
            "internalDate": "100",
            "payload": {"headers": [{"name": "Subject", "value": "Old"}]},
        },
        "new": {
            "id": "new",
            "threadId": "thread-new",
            "internalDate": "200",
            "payload": {"headers": [{"name": "Subject", "value": "New"}]},
        },
    }
    monkeypatch.setattr(
        search,
        "fetch_message_metadata",
        lambda _service, message_id: metadata_by_id[message_id],
    )

    service = FakeGmailService({"messages": [{"id": "old"}, {"id": "new"}]})

    bank_email = search.find_bank_email(service)

    assert bank_email is not None
    assert bank_email.message_id == "new"
    assert bank_email.subject == "New"
