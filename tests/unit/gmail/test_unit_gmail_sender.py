import base64
import email

import pytest

from src.integrations.gmail.exceptions import GmailSendError
from src.integrations.gmail.gmail_sender import DRY_RUN_FAKE_MESSAGE_ID, GmailSender


def _decode_raw(body: dict) -> email.message.Message:
    return email.message_from_bytes(base64.urlsafe_b64decode(body["raw"]))


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

    def send(self, userId: str, body: dict) -> _FakeSendCall:
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

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.get_gmail_service", lambda _tid: service)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)
    monkeypatch.setattr(
        "src.integrations.gmail.gmail_sender.EmailBuilder.build_email",
        lambda self, **kwargs: build_calls.append(kwargs) or b"mime-bytes",
    )

    message_id = GmailSender(telegram_id=123).send_email("recipient@example.com", "Invoice", "Body", [attachment])

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

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.get_gmail_service", lambda _tid: pytest.fail("service should not be created in dry run"))
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", fake_get_optional_env)

    message_id = GmailSender(telegram_id=123).send_email("recipient@example.com", "Invoice", "Body", [attachment])

    assert message_id == DRY_RUN_FAKE_MESSAGE_ID


def test_send_email_wraps_api_failure(monkeypatch, tmp_path) -> None:
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"pdf-bytes")
    service = _FakeService(RuntimeError("boom"))

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.get_gmail_service", lambda _tid: service)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EmailBuilder.build_email", lambda self, **kwargs: b"mime-bytes")

    with pytest.raises(GmailSendError, match="Failed to send email via Gmail API"):
        GmailSender(telegram_id=123).send_email("recipient@example.com", "Invoice", "Body", [attachment])


# ---------------------------------------------------------------------------
# send_reply
# ---------------------------------------------------------------------------


def test_send_reply_puts_thread_id_in_api_body(monkeypatch, tmp_path) -> None:
    attachment = tmp_path / "doc.pdf"
    attachment.write_bytes(b"pdf-bytes")
    service = _FakeService({"id": "reply-msg-1"})

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EmailBuilder.build_email", lambda self, **kwargs: b"mime-bytes")

    message_id = GmailSender(telegram_id=123, service=service).send_reply(
        thread_id="thread-abc",
        to_email="bank@example.com",
        subject="Re: Payment",
        body="Dobar dan.",
        attachments=[attachment],
    )

    assert message_id == "reply-msg-1"
    sent = service.users_client.messages_client.sent_bodies[0]
    assert sent["threadId"] == "thread-abc"
    assert "raw" in sent


def test_send_reply_dry_run(monkeypatch, tmp_path) -> None:
    def fake_get_optional_env(name: str, default: str) -> str:
        return "true" if name == "EMAIL_DRY_RUN" else default

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", fake_get_optional_env)

    message_id = GmailSender(telegram_id=123).send_reply(thread_id="t-1", to_email="a@b.com", subject="Re: s", body="b")

    assert message_id == DRY_RUN_FAKE_MESSAGE_ID


def test_send_reply_wraps_api_failure(monkeypatch, tmp_path) -> None:
    service = _FakeService(RuntimeError("network error"))

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)
    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EmailBuilder.build_email", lambda self, **kwargs: b"mime-bytes")

    with pytest.raises(GmailSendError, match="Failed to send email via Gmail API"):
        GmailSender(telegram_id=123, service=service).send_reply(thread_id="t-1", to_email="a@b.com", subject="Re: s", body="b")


# ---------------------------------------------------------------------------
# Реальная сборка MIME (EmailBuilder не замокан)
# ---------------------------------------------------------------------------


def test_send_email_real_mime_contains_attachment_filename(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake content")
    service = _FakeService({"id": "msg-mime-1"})

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)

    GmailSender(telegram_id=123, service=service).send_email(
        to_email="company@example.com",
        subject="Invoice may'26",
        body="Добрый день.",
        attachments=[pdf],
    )

    sent = service.users_client.messages_client.sent_bodies[0]
    parsed = _decode_raw(sent)
    assert parsed["To"] == "company@example.com"
    assert parsed["Subject"] == "Invoice may'26"
    filenames = [part.get_filename() for part in parsed.walk() if part.get_filename()]
    assert "invoice.pdf" in filenames


def test_send_reply_real_mime_thread_id_and_three_attachments(monkeypatch, tmp_path) -> None:
    files = [tmp_path / name for name in ("invoice.pdf", "confirmation.pdf", "conversion.pdf")]
    for f in files:
        f.write_bytes(b"%PDF fake")
    service = _FakeService({"id": "msg-mime-2"})

    monkeypatch.setattr("src.integrations.gmail.gmail_sender.EnvVar.get_optional_env", lambda name, default: default)

    GmailSender(telegram_id=123, service=service).send_reply(
        thread_id="thread-bank-456",
        to_email="bank@rs.com",
        subject="Re: Obaveštenje",
        body="Dobar dan.",
        attachments=files,
    )

    sent = service.users_client.messages_client.sent_bodies[0]
    assert sent["threadId"] == "thread-bank-456"
    parsed = _decode_raw(sent)
    filenames = [part.get_filename() for part in parsed.walk() if part.get_filename()]
    assert len(filenames) == 3
