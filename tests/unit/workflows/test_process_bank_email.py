from src.integrations.gmail.gmail_models import BankEmail
from src.workflows.bricks import fetch_bank_email


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

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: None)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: calls.append("download"))
    monkeypatch.setattr(fetch_bank_email, "mark_as_processed", lambda _message_id: calls.append("mark"))

    fetch_bank_email.fetch_bank_email_workflow()

    assert calls == []


def test_process_bank_email_workflow_skips_processed_email(monkeypatch) -> None:
    calls = []
    bank_email = build_bank_email()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: bank_email)
    monkeypatch.setattr(fetch_bank_email, "is_processed", lambda _message_id: True)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda _email: calls.append("download"))
    monkeypatch.setattr(fetch_bank_email, "mark_as_processed", lambda _message_id: calls.append("mark"))

    fetch_bank_email.fetch_bank_email_workflow()

    assert calls == []


def test_process_bank_email_workflow_downloads_and_marks_new_email(monkeypatch) -> None:
    calls = []
    bank_email = build_bank_email()

    monkeypatch.setattr(fetch_bank_email, "get_gmail_service", lambda: object())
    monkeypatch.setattr(fetch_bank_email, "find_bank_email", lambda _service: bank_email)
    monkeypatch.setattr(fetch_bank_email, "is_processed", lambda _message_id: False)
    monkeypatch.setattr(fetch_bank_email, "download_attachments", lambda email: calls.append(("download", email.message_id)))
    monkeypatch.setattr(fetch_bank_email, "mark_as_processed", lambda message_id: calls.append(("mark", message_id)))

    fetch_bank_email.fetch_bank_email_workflow()

    assert calls == [
        ("download", "message-123"),
        ("mark", "message-123"),
    ]
