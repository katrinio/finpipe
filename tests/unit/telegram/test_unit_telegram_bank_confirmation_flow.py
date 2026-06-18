from pathlib import Path
from types import SimpleNamespace

from src.integrations.gmail.gmail_models import BankEmail
from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.ui.buttons import DocumentsMenuButtons
from src.integrations.telegram.ui.menu.document_menu import build_bank_confirmation_menu
from src.integrations.telegram.ui.messages import BankMessages
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from tests.fakes.fake_telegram import FakeTelegramClient


def test_bank_confirmation_button_opens_submenu(tmp_path: Path) -> None:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    bot.process_update(
        {
            "update_id": 11,
            "message": {
                "text": DocumentsMenuButtons.BANK_CONFIRMATION,
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert telegram_client.sent_messages == [BankMessages.Menu.TITLE]
    assert telegram_client.sent_message_payloads == [(123, BankMessages.Menu.TITLE, build_bank_confirmation_menu())]


def test_bank_confirmation_upload_button_sets_waiting_state(tmp_path: Path) -> None:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    bot.handlers.document_handler.start_bank_confirmation_upload(123)

    assert telegram_client.sent_messages == [BankMessages.Menu.UPLOAD]
    assert telegram_client.sent_message_payloads == [(123, BankMessages.Menu.UPLOAD, build_bank_confirmation_menu())]


def test_manual_bank_confirmation_upload_requires_ready_profile(tmp_path: Path, monkeypatch) -> None:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.SystemStatusService.get_status",
        lambda _telegram_id: SimpleNamespace(company=True, bank_details=True),
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.Signature.is_usable", lambda _telegram_id: False)

    bot.handlers.document_handler.handle_bank_confirmation_upload(123, "bank.pdf", 42, b"%PDF-1.7\n")

    assert telegram_client.sent_messages == [BankMessages.Validation.SIGNATURE_REQUIRED]
    assert telegram_client.sent_message_payloads == [
        (123, BankMessages.Validation.SIGNATURE_REQUIRED, build_bank_confirmation_menu()),
    ]


def test_manual_bank_confirmation_upload_sends_filled_pdf(tmp_path: Path, monkeypatch) -> None:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    filled_pdf = tmp_path / "filled.pdf"
    filled_pdf.write_bytes(b"%PDF-1.7\nfilled")

    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.SystemStatusService.get_status",
        lambda _telegram_id: SimpleNamespace(company=True, bank_details=True),
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.Signature.is_usable", lambda _telegram_id: True)
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.extract_amount", lambda _pdf: 42.0)
    monkeypatch.setattr(
        bot.handlers.document_handler,
        "_fill_bank_confirmation_pdf",
        lambda _telegram_id, _input_pdf, _amount: filled_pdf,
    )

    bot.handlers.document_handler.handle_bank_confirmation_upload(123, "bank.pdf", 42, b"%PDF-1.7\n")

    assert telegram_client.sent_documents == [(123, str(filled_pdf))]
    assert telegram_client.sent_messages[-1] == BankMessages.Generation.FILLED
    assert bot.handlers.state_service.get_state(123) is None


def test_check_bank_email_reports_found(tmp_path: Path, monkeypatch) -> None:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.get_gmail_service", lambda: object())
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.find_bank_email",
        lambda _service, **_kwargs: BankEmail(
            subject="Bank payment confirmation",
            sender="bank@example.com",
            date="Fri, 17 Jun 2026",
            message_id="msg-1",
            thread_id="thr-1",
        ),
    )

    bot.handlers.document_handler.check_bank_email(123)

    assert telegram_client.sent_messages[0] == BankMessages.Search.CHECKING
    assert BankMessages.Search.FOUND in telegram_client.sent_messages[-1]
    assert "bank@example.com" in telegram_client.sent_messages[-1]


def test_get_and_process_bank_email_sends_original_and_filled(tmp_path: Path, monkeypatch) -> None:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    original_pdf = tmp_path / "original.pdf"
    original_pdf.write_bytes(b"%PDF-1.7\noriginal")
    filled_pdf = tmp_path / "filled.pdf"
    filled_pdf.write_bytes(b"%PDF-1.7\nfilled")

    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.fetch_bank_email_workflow",
        lambda **_kwargs: original_pdf,
    )
    monkeypatch.setattr(
        "src.integrations.telegram.handlers.document_handlers.SystemStatusService.get_status",
        lambda _telegram_id: SimpleNamespace(company=True, bank_details=True),
    )
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.Signature.is_usable", lambda _telegram_id: True)
    monkeypatch.setattr("src.integrations.telegram.handlers.document_handlers.extract_amount", lambda _pdf: 77.7)
    monkeypatch.setattr(
        bot.handlers.document_handler,
        "_fill_bank_confirmation_pdf",
        lambda _telegram_id, _input_pdf, _amount: filled_pdf,
    )

    bot.handlers.document_handler.get_and_process_bank_email(123)

    assert telegram_client.sent_documents == [(123, str(original_pdf)), (123, str(filled_pdf))]
    assert telegram_client.sent_messages[-1] == BankMessages.Generation.ORIGINAL_AND_FILLED
