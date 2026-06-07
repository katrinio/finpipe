import importlib
import sys
import types
from pathlib import Path

from src.constants import Message

sys.modules.setdefault("src.integrations.telegram.client", types.SimpleNamespace(TelegramClient=object))
sys.modules.setdefault("src.logging_config", types.SimpleNamespace(configure_logging=lambda: None))
sys.modules.setdefault("src.services.bank.bank_extract", types.SimpleNamespace(extract_amount=lambda _path: 0.0))
sys.modules.setdefault(
    "src.storage.dependencies",
    types.SimpleNamespace(build_storage_dependencies=lambda: types.SimpleNamespace(invoice_history=object(), processed_messages=object())),
)
sys.modules.setdefault(
    "src.utils.credentials",
    types.SimpleNamespace(EnvVar=types.SimpleNamespace(get_dotenv=lambda: None)),
)
sys.modules.setdefault(
    "src.workflows.bricks.fetch_bank_email",
    types.SimpleNamespace(fetch_bank_email_workflow=lambda **_kwargs: None),
)
sys.modules.setdefault(
    "src.workflows.bricks.fill_bank_pdf",
    types.SimpleNamespace(fill_bank_pdf_with_data=lambda *_args, **_kwargs: None),
)
sys.modules.setdefault(
    "src.workflows.bricks.generate_invoice",
    types.SimpleNamespace(generate_invoice_pdf=lambda **_kwargs: None),
)
sys.modules.setdefault(
    "src.workflows.bricks.generate_transfer_request",
    types.SimpleNamespace(generate_transfer_request_pdf=lambda **_kwargs: None),
)

process_bank_request = importlib.import_module("src.workflows.process_bank_request")


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


def test_main_returns_early_when_no_new_bank_email(monkeypatch) -> None:
    calls: list[str] = []
    telegram_client = FakeTelegramClient()
    storage = FakeStorage()

    monkeypatch.setattr(process_bank_request, "configure_logging", lambda: calls.append("configure_logging"))
    monkeypatch.setattr(process_bank_request.EnvVar, "get_dotenv", lambda: calls.append("get_dotenv"))
    monkeypatch.setattr(process_bank_request, "build_storage_dependencies", lambda: storage)
    monkeypatch.setattr(process_bank_request, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(
        process_bank_request,
        "fetch_bank_email_workflow",
        lambda **kwargs: calls.append("fetch") or None,
    )
    monkeypatch.setattr(process_bank_request, "extract_amount", lambda _path: calls.append("extract_amount"))
    monkeypatch.setattr(process_bank_request, "fill_bank_pdf_with_data", lambda *_args, **_kwargs: calls.append("fill_bank_pdf"))
    monkeypatch.setattr(process_bank_request, "generate_transfer_request_pdf", lambda **_kwargs: calls.append("transfer_request"))
    monkeypatch.setattr(process_bank_request, "generate_invoice_pdf", lambda **_kwargs: calls.append("invoice"))

    result = process_bank_request.main()

    assert result == 0
    assert calls == ["configure_logging", "get_dotenv", "fetch"]
    assert telegram_client.messages == [
        Message.START,
        Message.NO_NEW_BANK_EMAIL,
    ]
    assert telegram_client.documents == []


def test_main_generates_all_documents_and_sends_bank_response(monkeypatch) -> None:
    calls: list[object] = []
    telegram_client = FakeTelegramClient()
    storage = FakeStorage()
    bank_template_path = Path("attachments/bank-form.pdf")
    bank_pdf_path = Path("output/bank/filled.pdf")
    transfer_request_pdf_path = Path("output/transfer_request/request.pdf")
    invoice_pdf_path = Path("output/invoices/invoice.pdf")

    monkeypatch.setattr(process_bank_request, "configure_logging", lambda: calls.append("configure_logging"))
    monkeypatch.setattr(process_bank_request.EnvVar, "get_dotenv", lambda: calls.append("get_dotenv"))
    monkeypatch.setattr(process_bank_request, "build_storage_dependencies", lambda: storage)
    monkeypatch.setattr(process_bank_request, "TelegramClient", lambda: telegram_client)
    monkeypatch.setattr(
        process_bank_request,
        "fetch_bank_email_workflow",
        lambda **kwargs: calls.append(("fetch", kwargs["processed_message_repository"])) or bank_template_path,
    )
    monkeypatch.setattr(
        process_bank_request,
        "extract_amount",
        lambda path: calls.append(("extract_amount", path)) or 123.4,
    )
    monkeypatch.setattr(
        process_bank_request,
        "fill_bank_pdf_with_data",
        lambda path, amount: calls.append(("fill_bank_pdf", path, amount)) or bank_pdf_path,
    )
    monkeypatch.setattr(
        process_bank_request,
        "generate_transfer_request_pdf",
        lambda amount: calls.append(("transfer_request", amount)) or transfer_request_pdf_path,
    )
    monkeypatch.setattr(
        process_bank_request,
        "generate_invoice_pdf",
        lambda **kwargs: calls.append(("invoice", kwargs["amount"], kwargs["invoice_history_repository"])) or invoice_pdf_path,
    )

    result = process_bank_request.main()

    assert result == 0
    assert calls == [
        "configure_logging",
        "get_dotenv",
        ("fetch", storage.processed_messages),
        ("extract_amount", bank_template_path),
        ("fill_bank_pdf", bank_template_path, 123.4),
        ("transfer_request", "123.40"),
        ("invoice", "123.40", storage.invoice_history),
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
