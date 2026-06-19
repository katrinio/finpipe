"""Unit-тесты: Telegram-флоу кнопок «Отправить компании» / «Не сейчас»."""

from pathlib import Path
from unittest.mock import patch

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.messages.invoice_messages import InvoiceMessages
from src.integrations.telegram.ui.buttons import InvoiceMenuButtons
from src.integrations.telegram.ui.menu.document_menu import build_invoice_menu
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from tests.fakes.fake_telegram import FakeTelegramClient

_HANDLERS_MODULE = "src.integrations.telegram.handlers.document_handlers"


def _make_bot() -> tuple[TelegramBot, FakeTelegramClient]:
    storage = build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)
    return bot, telegram_client


def _press(bot: TelegramBot, text: str) -> None:
    bot.process_update(
        {
            "update_id": 1,
            "message": {"text": text, "from": {"id": 123, "username": "alice"}},
        }
    )


def test_send_to_company_calls_send_invoice_email_and_shows_success(tmp_path: Path) -> None:
    bot, telegram_client = _make_bot()
    sent: list[int] = []

    with patch(f"{_HANDLERS_MODULE}.send_invoice_email", lambda tid: sent.append(tid)):
        _press(bot, InvoiceMenuButtons.SEND_TO_COMPANY)

    assert sent == [123]
    assert InvoiceMessages.Generation.SENT_TO_COMPANY in telegram_client.sent_messages
    assert telegram_client.sent_message_payloads[-1] == (
        123,
        InvoiceMessages.Generation.SENT_TO_COMPANY,
        build_invoice_menu(),
    )


def test_send_to_company_shows_error_on_failure(tmp_path: Path) -> None:
    from src.services.invoice.exceptions import InvoiceError

    bot, telegram_client = _make_bot()

    with patch(f"{_HANDLERS_MODULE}.send_invoice_email", side_effect=InvoiceError("нет профиля")):
        _press(bot, InvoiceMenuButtons.SEND_TO_COMPANY)

    assert any("нет профиля" in m for m in telegram_client.sent_messages)
    assert telegram_client.sent_message_payloads[-1][2] == build_invoice_menu()


def test_skip_send_discards_pdf_and_shows_sent_message(tmp_path: Path) -> None:
    bot, telegram_client = _make_bot()
    discarded: list[bool] = []

    with patch(f"{_HANDLERS_MODULE}.discard_invoice_pdf", lambda: discarded.append(True)):
        _press(bot, InvoiceMenuButtons.SKIP_SEND)

    assert discarded == [True]
    assert InvoiceMessages.Generation.SENT in telegram_client.sent_messages
