from io import BytesIO
from types import SimpleNamespace
from typing import Any, cast

import pytest
from pypdf import PdfWriter

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.handlers import document_handlers
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.buttons import DocumentsMenuButtons
from src.integrations.telegram.ui.menu.document_menu import build_document_menu
from src.integrations.telegram.ui.messages import BankMessages
from src.storage.orm import Signature, UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from tests.fakes.fake_storage import FakeTelegramUpdateStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def _pdf_bytes() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


def _build_ready_bot(monkeypatch: pytest.MonkeyPatch, telegram: FakeTelegramClient) -> TelegramBot:
    monkeypatch.setattr(CompanyProfile, "get_by_owner", classmethod(lambda cls, telegram_id: SimpleNamespace()))
    monkeypatch.setattr(BankDetails, "get_by_owner", classmethod(lambda cls, telegram_id: SimpleNamespace()))
    monkeypatch.setattr(Signature, "is_usable", classmethod(lambda cls, telegram_id: True))

    bot = TelegramBot(telegram=cast(TelegramClient, telegram), owner_telegram_id=123)
    bot.update_storage = cast(Any, FakeTelegramUpdateStorage())
    return bot


def test_document_menu_contains_bank_confirmation_and_conversion_request() -> None:
    menu = build_document_menu()
    buttons = {button["text"] for row in menu["keyboard"] for button in row}

    assert DocumentsMenuButtons.BANK_TRANSFER_CONFIRMATION in buttons
    assert DocumentsMenuButtons.CONVERSION_REQUEST in buttons


def test_bank_confirmation_button_starts_pdf_upload_state(monkeypatch: pytest.MonkeyPatch) -> None:
    telegram = FakeTelegramClient()
    bot = _build_ready_bot(monkeypatch, telegram)

    assert bot.handle_message(DocumentsMenuButtons.BANK_TRANSFER_CONFIRMATION, telegram_id=123, username="alice") is True

    assert bot.handlers.state_service.get_state(123) == UserState.WAITING_BANK_DOCUMENT_UPLOAD
    assert telegram.sent_message_payloads[-1] == (123, BankMessages.Confirmation.UPLOAD, build_document_menu())


def test_bank_pdf_upload_generates_document_and_clears_state(monkeypatch: pytest.MonkeyPatch) -> None:
    source_pdf = _pdf_bytes()
    telegram = FakeTelegramClient(files={"bank-file-id": source_pdf})
    bot = _build_ready_bot(monkeypatch, telegram)
    delivered: list[tuple[int, bytes]] = []

    def fake_delivery(client: TelegramClient, chat_id: int, file_bytes: bytes) -> None:
        assert client is telegram
        delivered.append((chat_id, file_bytes))

    monkeypatch.setattr(document_handlers, "generate_and_send_bank_confirmation", fake_delivery)

    bot.handle_message(DocumentsMenuButtons.BANK_TRANSFER_CONFIRMATION, telegram_id=123, username="alice")
    bot.process_update(
        {
            "update_id": 42,
            "message": {
                "document": {
                    "file_id": "bank-file-id",
                    "file_name": "bank.pdf",
                    "file_size": len(source_pdf),
                },
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert delivered == [(123, source_pdf)]
    assert bot.handlers.state_service.get_state(123) is None
    assert telegram.sent_messages[-2:] == [BankMessages.Confirmation.IN_PROGRESS, BankMessages.Confirmation.SENT]


def test_invalid_bank_upload_keeps_waiting_state(monkeypatch: pytest.MonkeyPatch) -> None:
    telegram = FakeTelegramClient(files={"bank-file-id": b"not-a-pdf"})
    bot = _build_ready_bot(monkeypatch, telegram)

    bot.handle_message(DocumentsMenuButtons.BANK_TRANSFER_CONFIRMATION, telegram_id=123, username="alice")
    bot.process_update(
        {
            "update_id": 43,
            "message": {
                "document": {
                    "file_id": "bank-file-id",
                    "file_name": "bank.pdf",
                    "file_size": 9,
                },
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert bot.handlers.state_service.get_state(123) == UserState.WAITING_BANK_DOCUMENT_UPLOAD
    assert telegram.sent_messages[-1] == BankMessages.Validation.INVALID_PDF


def test_conversion_request_uses_last_bank_amount_and_sends_result(monkeypatch: pytest.MonkeyPatch) -> None:
    telegram = FakeTelegramClient()
    bot = _build_ready_bot(monkeypatch, telegram)
    delivered: list[tuple[int, float]] = []

    monkeypatch.setattr(
        UserConfig,
        "get_by_owner",
        classmethod(lambda cls, telegram_id: SimpleNamespace(bank_received_amount_eur=1200.5)),
    )
    monkeypatch.setattr(
        document_handlers,
        "generate_and_send_conversion_request",
        lambda client, chat_id, amount: delivered.append((chat_id, amount)),
    )

    assert bot.handle_message(DocumentsMenuButtons.CONVERSION_REQUEST, telegram_id=123, username="alice") is True

    assert delivered == [(123, 1200.5)]
    assert telegram.sent_messages[-2:] == [BankMessages.ConversionRequest.IN_PROGRESS, BankMessages.ConversionRequest.SENT]


def test_conversion_request_requires_bank_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    telegram = FakeTelegramClient()
    bot = _build_ready_bot(monkeypatch, telegram)
    monkeypatch.setattr(UserConfig, "get_by_owner", classmethod(lambda cls, telegram_id: None))

    bot.handle_message(DocumentsMenuButtons.CONVERSION_REQUEST, telegram_id=123, username="alice")

    assert telegram.sent_message_payloads[-1] == (123, BankMessages.Validation.NO_BANK_AMOUNT, build_document_menu())
