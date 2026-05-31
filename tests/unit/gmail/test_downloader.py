import base64
import logging

from src.integrations.gmail import downloader
from src.integrations.gmail.gmail_models import BankEmail


class FakeExecute:
    def __init__(self, response: dict) -> None:
        self.response = response

    def execute(self) -> dict:
        return self.response


class FakeAttachmentsApi:
    def __init__(self, response: dict) -> None:
        self.response = response

    def get(self, **_kwargs) -> FakeExecute:
        return FakeExecute(self.response)


class FakeMessagesApi:
    def __init__(self, message_response: dict, attachment_response: dict) -> None:
        self.message_response = message_response
        self.attachment_response = attachment_response

    def get(self, **_kwargs) -> FakeExecute:
        return FakeExecute(self.message_response)

    def attachments(self) -> FakeAttachmentsApi:
        return FakeAttachmentsApi(self.attachment_response)


class FakeUsersApi:
    def __init__(self, messages_api: FakeMessagesApi) -> None:
        self.messages_api = messages_api

    def messages(self) -> FakeMessagesApi:
        return self.messages_api


class FakeGmailService:
    def __init__(self, message_response: dict, attachment_response: dict) -> None:
        self.messages_api = FakeMessagesApi(message_response, attachment_response)

    def users(self) -> FakeUsersApi:
        return FakeUsersApi(self.messages_api)


def build_bank_email() -> BankEmail:
    return BankEmail(
        subject="Bank payment",
        sender="bank@example.com",
        date="Fri, 29 May 2026",
        message_id="message-123",
        thread_id="thread-123",
    )


def test_download_attachments_saves_pdf_attachment(tmp_path, monkeypatch) -> None:
    message_response = {
        "payload": {
            "parts": [
                {
                    "filename": "bank-form.pdf",
                    "body": {"attachmentId": "attachment-123"},
                }
            ],
        },
    }
    attachment_response = {
        "data": base64.urlsafe_b64encode(b"pdf-bytes").decode("utf-8"),
    }
    service = FakeGmailService(message_response, attachment_response)

    monkeypatch.setattr(downloader, "get_gmail_service", lambda: service)
    monkeypatch.setattr(downloader.Dir, "ATTACHMENTS", tmp_path)
    monkeypatch.setattr(downloader.Utils, "today", lambda: "2026-05-29")

    downloader.download_attachments(build_bank_email())

    assert (tmp_path / "bank-form-2026-05-29").read_bytes() == b"pdf-bytes"


def test_download_attachments_logs_warning_when_pdf_is_missing(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    message_response = {
        "payload": {
            "parts": [
                {
                    "filename": "notes.txt",
                    "body": {"attachmentId": "attachment-123"},
                }
            ],
        },
    }
    service = FakeGmailService(message_response, {})

    monkeypatch.setattr(downloader, "get_gmail_service", lambda: service)
    monkeypatch.setattr(downloader.Dir, "ATTACHMENTS", tmp_path)

    with caplog.at_level(logging.WARNING):
        downloader.download_attachments(build_bank_email())

    assert list(tmp_path.iterdir()) == []
    assert "No PDF attachments found" in caplog.text
