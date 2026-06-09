import importlib
from pathlib import Path
from typing import TypeVar

import pytest

from src.constants import Message

process_bank_request = importlib.import_module("src.workflows.prepare_bank_pdf")
T = TypeVar("T")


class FakeTelegramClient:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.documents: list[Path] = []

    def send_message(self, message: str) -> None:
        self.messages.append(message)

    def send_document(self, document_path: Path) -> None:
        self.documents.append(document_path)


class FakeStorage:
    def __init__(self) -> None:
        self.invoice_history = object()
        self.processed_messages = object()


def test_main_returns_early_when_no_new_bank_email(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    telegram_client = FakeTelegramClient()

    monkeypatch.setattr(process_bank_request, "configure_logging", lambda: calls.append("configure_logging"))
    monkeypatch.setattr(process_bank_request.EnvVar, "get_dotenv", lambda: calls.append("get_dotenv"))
    monkeypatch.setattr(process_bank_request, "build_storage_dependencies", lambda: FakeStorage())
    monkeypatch.setattr(process_bank_request, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(
        process_bank_request,
        "fetch_bank_email_workflow",
        lambda: _record_str_and_return(calls, "fetch", None),
    )
    monkeypatch.setattr(process_bank_request, "extract_amount", lambda _path: _record_call(calls, "extract_amount"))
    monkeypatch.setattr(process_bank_request, "fill_bank_pdf_with_data", lambda *_args, **_kwargs: _record_call(calls, "fill_bank_pdf"))
    monkeypatch.setattr(process_bank_request, "generate_transfer_request_pdf", lambda **_kwargs: _record_call(calls, "transfer_request"))
    monkeypatch.setattr(process_bank_request, "generate_invoice_pdf", lambda **_kwargs: _record_call(calls, "invoice"))

    result = process_bank_request.main()

    assert result == 0
    assert calls == ["configure_logging", "get_dotenv", "fetch"]
    assert telegram_client.messages == [
        Message.START,
        Message.NO_NEW_BANK_EMAIL,
    ]
    assert telegram_client.documents == []


def test_main_generates_all_documents_and_sends_bank_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    telegram_client = FakeTelegramClient()
    bank_template_path = Path("attachments/bank-form.pdf")
    bank_pdf_path = Path("output/bank/filled.pdf")
    transfer_request_pdf_path = Path("output/transfer_request/request.pdf")
    invoice_pdf_path = Path("output/invoices/invoice.pdf")

    monkeypatch.setattr(process_bank_request, "configure_logging", lambda: calls.append("configure_logging"))
    monkeypatch.setattr(process_bank_request.EnvVar, "get_dotenv", lambda: calls.append("get_dotenv"))
    monkeypatch.setattr(process_bank_request, "build_storage_dependencies", lambda: FakeStorage())
    monkeypatch.setattr(process_bank_request, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(
        process_bank_request,
        "fetch_bank_email_workflow",
        lambda: _record_call_and_return(calls, "fetch", bank_template_path),
    )
    monkeypatch.setattr(
        process_bank_request,
        "extract_amount",
        lambda path: _record_tuple_and_return(calls, ("extract_amount", path), 123.4),
    )
    monkeypatch.setattr(
        process_bank_request,
        "fill_bank_pdf_with_data",
        lambda path, amount: _record_tuple_and_return(calls, ("fill_bank_pdf", path, amount), bank_pdf_path),
    )
    monkeypatch.setattr(
        process_bank_request,
        "generate_transfer_request_pdf",
        lambda amount: _record_tuple_and_return(calls, ("transfer_request", amount), transfer_request_pdf_path),
    )
    monkeypatch.setattr(
        process_bank_request,
        "generate_invoice_pdf",
        lambda **kwargs: _record_tuple_and_return(calls, ("invoice", kwargs["amount"]), invoice_pdf_path),
    )

    result = process_bank_request.main()

    assert result == 0
    assert calls == [
        "configure_logging",
        "get_dotenv",
        "fetch",
        ("extract_amount", bank_template_path),
        ("fill_bank_pdf", bank_template_path, 123.4),
        ("transfer_request", "123.40"),
        ("invoice", "123.40"),
    ]
    assert telegram_client.messages == [
        Message.START,
        Message.EMAIL_FETCHING_COMPLETED,
        Message.BANK_PDF_FILLED,
        Message.TRANSACTION_REQUEST_GENERATED,
        Message.INVOICE_GENERATED,
        Message.BANK_RESPONSE,
    ]
    assert telegram_client.documents == [
        invoice_pdf_path,
        transfer_request_pdf_path,
        bank_pdf_path,
    ]


def _record_call(calls: list[str], value: str) -> None:
    calls.append(value)


def _record_str_and_return[T](calls: list[str], value: str, result: T) -> T:
    calls.append(value)
    return result


def _record_call_and_return[T](calls: list[object], value: object, result: T) -> T:
    calls.append(value)
    return result


def _record_tuple_and_return[T](calls: list[object], value: object, result: T) -> T:
    calls.append(value)
    return result
