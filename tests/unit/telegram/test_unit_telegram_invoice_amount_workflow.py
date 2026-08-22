from pathlib import Path

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.buttons import InvoiceMenuButtons
from src.integrations.telegram.messages import InvoiceMessages
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.document_menu import build_invoice_menu
from src.storage.orm import UserConfig
from tests.fakes.fake_telegram import FakeTelegramClient


def test_invoice_amount_button_starts_waiting_state_and_prompts(tmp_path: Path) -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(telegram=telegram_client, owner_telegram_id=123)

    bot.process_update(
        {
            "update_id": 11,
            "message": {
                "text": InvoiceMenuButtons.SET_INVOICE_AMOUNT,
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert bot.handlers.state_service.get_state(123) == UserState.WAITING_INVOICE_AMOUNT
    assert telegram_client.sent_messages == [InvoiceMessages.Amount.INPUT]
    assert telegram_client.sent_message_payloads == [(123, InvoiceMessages.Amount.INPUT, build_invoice_menu())]


def test_invoice_amount_state_saves_valid_number_and_clears_state(tmp_path: Path) -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(telegram=telegram_client, owner_telegram_id=123)

    bot.process_update(
        {
            "update_id": 11,
            "message": {
                "text": InvoiceMenuButtons.SET_INVOICE_AMOUNT,
                "from": {"id": 123, "username": "alice"},
            },
        }
    )
    bot.process_update(
        {
            "update_id": 12,
            "message": {
                "text": "1500",
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    config = UserConfig.get_by_owner(123)

    assert config is not None
    assert config.invoice_amount_eur == 1500
    assert bot.handlers.state_service.get_state(123) is None
    assert telegram_client.sent_messages == [
        InvoiceMessages.Amount.INPUT,
        InvoiceMessages.Amount.SAVED.format(1500),
    ]
    assert telegram_client.sent_message_payloads == [
        (123, InvoiceMessages.Amount.INPUT, build_invoice_menu()),
        (123, InvoiceMessages.Amount.SAVED.format(1500), build_invoice_menu()),
    ]


def test_invoice_amount_state_rejects_non_numeric_input_and_keeps_state(tmp_path: Path) -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(telegram=telegram_client, owner_telegram_id=123)

    bot.process_update(
        {
            "update_id": 11,
            "message": {
                "text": InvoiceMenuButtons.SET_INVOICE_AMOUNT,
                "from": {"id": 123, "username": "alice"},
            },
        }
    )
    bot.process_update(
        {
            "update_id": 12,
            "message": {
                "text": "1,500",
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    config = UserConfig.get_by_owner(123)

    assert config is None or config.invoice_amount_eur is None
    assert bot.handlers.state_service.get_state(123) == UserState.WAITING_INVOICE_AMOUNT
    assert telegram_client.sent_messages == [
        InvoiceMessages.Amount.INPUT,
        "❌ Сумма должна содержать только цифры.\nПример: 1500",
    ]
    assert telegram_client.sent_message_payloads == [
        (123, InvoiceMessages.Amount.INPUT, build_invoice_menu()),
        (123, "❌ Сумма должна содержать только цифры.\nПример: 1500", build_invoice_menu()),
    ]


def test_get_invoice_amount_reports_missing_value(tmp_path: Path) -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(telegram=telegram_client, owner_telegram_id=123)

    bot.handlers.document_handler.get_invoice_amount(123)

    assert telegram_client.sent_messages == [
        InvoiceMessages.Validation.NO_INVOICE_AMOUNT,
    ]
    assert telegram_client.sent_message_payloads == [
        (123, InvoiceMessages.Validation.NO_INVOICE_AMOUNT, build_invoice_menu()),
    ]
