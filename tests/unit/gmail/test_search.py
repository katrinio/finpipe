import pytest

from src.integrations.gmail import search


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


@pytest.mark.skip(reason="Ждет переноса энвов.")
def test_build_bank_email_query_uses_required_filters(monkeypatch) -> None:
    monkeypatch.setattr(search, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("BANK_EMAIL_SUBJECT", 'KATRIN "TORSUNOVA" PR')
    monkeypatch.setenv("BANK_EMAIL_FROM", 'bank"sender@example.com')

    query = search.build_bank_email_query()

    assert query == ('subject:"KATRIN \\"TORSUNOVA\\" PR" from:"bank\\"sender@example.com" newer_than:30d has:attachment')


@pytest.mark.skip(reason="Ждет переноса энвов.")
def test_build_bank_email_query_requires_subject(monkeypatch) -> None:
    monkeypatch.setattr(search, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.delenv("BANK_EMAIL_SUBJECT", raising=False)
    monkeypatch.setenv("BANK_EMAIL_FROM", "bank@example.com")

    with pytest.raises(RuntimeError, match="BANK_EMAIL_SUBJECT"):
        search.build_bank_email_query()


@pytest.mark.skip(reason="Ждет переноса энвов.")
def test_build_bank_email_query_requires_sender(monkeypatch) -> None:
    monkeypatch.setattr(search, "load_dotenv", lambda *_args, **_kwargs: None)
    monkeypatch.setenv("BANK_EMAIL_SUBJECT", "KATRIN TORSUNOVA PR")
    monkeypatch.delenv("BANK_EMAIL_FROM", raising=False)

    with pytest.raises(RuntimeError, match="BANK_EMAIL_FROM"):
        search.build_bank_email_query()


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
    monkeypatch.setattr(search, "build_bank_email_query", lambda: "query")
    service = FakeGmailService({"messages": []})

    assert search.find_bank_email(service) is None
    assert service.messages_api.list_kwargs == {
        "userId": "me",
        "q": "query",
        "maxResults": 10,
    }


def test_find_bank_email_selects_newest_message(monkeypatch) -> None:
    monkeypatch.setattr(search, "build_bank_email_query", lambda: "query")

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
