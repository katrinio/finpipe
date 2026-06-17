import importlib
from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class BankEmail:
    subject: str
    sender: str
    date: str
    message_id: str
    thread_id: str


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


def test_process_bank_email_workflow_returns_when_no_email(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    FakeProcessedMessage.reset()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service, **_kwargs: None)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: _record_call(calls, "download"))
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow(owner_telegram_id=123)

    assert result is None
    assert calls == []
    assert FakeProcessedMessage.is_processed_calls == []
    assert FakeProcessedMessage.mark_calls == []


def test_process_bank_email_workflow_skips_processed_email(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    bank_email = build_bank_email()
    FakeProcessedMessage.reset()
    FakeProcessedMessage.processed_ids = {bank_email.message_id}

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service, **_kwargs: bank_email)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: _record_call(calls, "download"))
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow(owner_telegram_id=123)

    assert result is None
    assert calls == []
    assert FakeProcessedMessage.mark_calls == []


def test_process_bank_email_workflow_downloads_and_marks_new_email(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    bank_email = build_bank_email()
    FakeProcessedMessage.reset()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service, **_kwargs: bank_email)
    monkeypatch.setattr(
        fetch_bank_email,
        "download_attachments",
        lambda email: _record_download(calls, email.message_id),
    )
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow(owner_telegram_id=123)

    assert result == "attachments/bank-form.pdf"
    assert calls == [("download", "message-123")]
    assert FakeProcessedMessage.mark_calls == ["message-123"]


def test_process_bank_email_workflow_does_not_mark_without_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    bank_email = build_bank_email()
    FakeProcessedMessage.reset()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service, **_kwargs: bank_email)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: None)
    monkeypatch.setattr(fetch_bank_email, "ProcessedMessage", FakeProcessedMessage)

    result = fetch_bank_email.fetch_bank_email_workflow(owner_telegram_id=123)

    assert result is None
    assert FakeProcessedMessage.mark_calls == []


def _record_call(calls: list[str], value: str) -> None:
    calls.append(value)


def _record_download(calls: list[tuple[str, str]], message_id: str) -> str:
    calls.append(("download", message_id))
    return "attachments/bank-form.pdf"
