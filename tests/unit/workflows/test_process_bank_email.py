import importlib
import sys
import types
from dataclasses import dataclass


@dataclass(frozen=True)
class BankEmail:
    subject: str
    sender: str
    date: str
    message_id: str
    thread_id: str


sys.modules.setdefault(
    "src.integrations.gmail",
    types.SimpleNamespace(BankEmail=BankEmail, get_gmail_service=lambda: object()),
)
sys.modules.setdefault(
    "src.integrations.gmail.downloader",
    types.SimpleNamespace(download_attachments=lambda _email: None),
)
sys.modules.setdefault(
    "src.integrations.gmail.search",
    types.SimpleNamespace(find_bank_email=lambda _service: None),
)
sys.modules.setdefault("src.logging_config", types.SimpleNamespace(configure_logging=lambda: None))

fetch_bank_email = importlib.import_module("src.workflows.tasks.fetch_bank_email")


class FakeProcessedMessage:
    processed_ids: set[str] = set()
    is_processed_calls: list[str] = []
    mark_calls: list[str] = []

    @classmethod
    def reset(cls) -> None:
        cls.processed_ids = set()
        cls.is_processed_calls = []
        cls.mark_calls = []

    @classmethod
    def is_processed(cls, message_id: str) -> bool:
        cls.is_processed_calls.append(message_id)
        return message_id in cls.processed_ids

    @classmethod
    def mark_as_processed(cls, message_id: str) -> None:
        cls.mark_calls.append(message_id)
        cls.processed_ids.add(message_id)


def build_bank_email(message_id: str = "message-123") -> BankEmail:
    return BankEmail(
        subject="Bank payment",
        sender="bank@example.com",
        date="Fri, 29 May 2026",
        message_id=message_id,
        thread_id="thread-123",
    )


def test_process_bank_email_workflow_returns_when_no_email(monkeypatch) -> None:
    calls = []
    FakeProcessedMessage.reset()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: None)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: calls.append("download"))
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow()

    assert result is None
    assert calls == []
    assert FakeProcessedMessage.is_processed_calls == []
    assert FakeProcessedMessage.mark_calls == []


def test_process_bank_email_workflow_skips_processed_email(monkeypatch) -> None:
    calls = []
    bank_email = build_bank_email()
    FakeProcessedMessage.reset()
    FakeProcessedMessage.processed_ids = {bank_email.message_id}

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: bank_email)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: calls.append("download"))
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow()

    assert result is None
    assert calls == []
    assert FakeProcessedMessage.mark_calls == []


def test_process_bank_email_workflow_downloads_and_marks_new_email(monkeypatch) -> None:
    calls = []
    bank_email = build_bank_email()
    FakeProcessedMessage.reset()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: bank_email)
    monkeypatch.setattr(
        fetch_bank_email,
        "download_attachments",
        lambda email: calls.append(("download", email.message_id)) or "attachments/bank-form.pdf",
    )
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow()

    assert result == "attachments/bank-form.pdf"
    assert calls == [("download", "message-123")]
    assert FakeProcessedMessage.mark_calls == ["message-123"]


def test_process_bank_email_workflow_does_not_mark_without_pdf(monkeypatch) -> None:
    bank_email = build_bank_email()
    FakeProcessedMessage.reset()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: bank_email)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: None)
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow()

    assert result is None
    assert FakeProcessedMessage.mark_calls == []
