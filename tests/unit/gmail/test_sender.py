import pytest

from src.integrations.gmail.exceptions import GmailSendError
from src.integrations.gmail.gmail_sender import DRY_RUN_FAKE_MESSAGE_ID, GmailSender


class _FakeSendCall:
    def __init__(self, response: dict | Exception) -> None:
        self.response = response
        self.payload = None

    def execute(self) -> dict:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class _FakeMessages:
    def __init__(self, response: dict | Exception) -> None:
        self.response = response
        self.sent_bodies: list[dict] = []

    def send(self, userId: str, body: dict) -> _FakeSendCall:  # noqa: N803
        self.sent_bodies.append(body)
        return _FakeSendCall(self.response)


class _FakeUsers:
    def __init__(self, response: dict | Exception) -> None:
        self.messages_client = _FakeMessages(response)

    def messages(self) -> _FakeMessages:
        return self.messages_client


class _FakeService:
    def __init__(self, response: dict | Exception) -> None:
        self.users_client = _FakeUsers(response)

    def users(self) -> _FakeUsers:
        return self.users_client


def test_send_email_successful_send(monkeypatch, tmp_path) -> None:
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"pdf-bytes")
    service = _FakeService({"id": "gmail-message-1"})
    build_calls: list[dict] = []

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.get_gmail_service", lambda: service)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)
    monkeypatch.setattr(
        "src.integrations.gmail.gmail_sender.EmailBuilder.build_email",
        lambda self, **kwargs: build_calls.append(kwargs) or b"mime-bytes",
    )

    message_id = GmailSender().send_email("recipient@example.com", "Invoice", "Body", [attachment])

    assert message_id == "gmail-message-1"
    assert build_calls == [
        {
            "to_email": "recipient@example.com",
            "subject": "Invoice",
            "body": "Body",
            "attachments": [attachment],
        }
    ]
    assert service.users_client.messages_client.sent_bodies == [{"raw": "bWltZS1ieXRlcw=="}]


def test_send_email_dry_run(monkeypatch, tmp_path) -> None:
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"pdf-bytes")

    def fake_get_optional_env(name: str, default: str) -> str:
        if name == "EMAIL_DRY_RUN":
            return "true"
        if name == "EMAIL_DRY_RUN_RECIPIENT":
            return "dry-run@example.com"
        return default

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.get_gmail_service", lambda: pytest.fail("service should not be created in dry run"))
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", fake_get_optional_env)

    message_id = GmailSender().send_email("recipient@example.com", "Invoice", "Body", [attachment])

    assert message_id == DRY_RUN_FAKE_MESSAGE_ID


def test_send_email_wraps_api_failure(monkeypatch, tmp_path) -> None:
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"pdf-bytes")
    service = _FakeService(RuntimeError("boom"))

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.get_gmail_service", lambda: service)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EmailBuilder.build_email", lambda self, **kwargs: b"mime-bytes")

    with pytest.raises(GmailSendError, match="Failed to send email via Gmail API"):
        GmailSender().send_email("recipient@example.com", "Invoice", "Body", [attachment])
