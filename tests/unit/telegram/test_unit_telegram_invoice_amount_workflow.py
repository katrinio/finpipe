from pathlib import Path

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.buttons import InvoiceMenuButtons
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser, UserConfig
from tests.fakes.fake_telegram import FakeTelegramClient


def test_invoice_amount_button_starts_waiting_state_and_prompts(tmp_path: Path) -> None:
    storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

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
    assert telegram_client.sent_messages == ["💰 Введите сумму Salary Invoice:"]
    assert telegram_client.sent_message_payloads == [(123, "💰 Введите сумму Salary Invoice:", None)]


def test_invoice_amount_state_saves_valid_number_and_clears_state(tmp_path: Path) -> None:
    storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

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
    assert config.invoice_amount == 1500
    assert bot.handlers.state_service.get_state(123) is None
    assert telegram_client.sent_messages == [
        "💰 Введите сумму Salary Invoice:",
        "✅ Сумма Salary Invoice сохранена: 1500 EUR",
    ]
    assert telegram_client.sent_message_payloads == [
        (123, "💰 Введите сумму Salary Invoice:", None),
        (123, "✅ Сумма Salary Invoice сохранена: 1500 EUR", None),
    ]


def test_invoice_amount_state_rejects_non_numeric_input_and_keeps_state(tmp_path: Path) -> None:
    storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

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

    assert config is None or config.invoice_amount is None
    assert bot.handlers.state_service.get_state(123) == UserState.WAITING_INVOICE_AMOUNT
    assert telegram_client.sent_messages == [
        "💰 Введите сумму Salary Invoice:",
        "❌ Сумма должна содержать только цифры.\nПример: 1500",
    ]
    assert telegram_client.sent_message_payloads == [
        (123, "💰 Введите сумму Salary Invoice:", None),
        (123, "❌ Сумма должна содержать только цифры.\nПример: 1500", None),
    ]


def test_get_invoice_amount_reports_missing_value(tmp_path: Path) -> None:
    storage = build_storage_dependencies(tmp_path / "storage.sqlite3")
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(storage, telegram=telegram_client)

    bot.handlers.document_handler.get_invoice_amount(123)

    assert telegram_client.sent_messages == [
        "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму».",
    ]
    assert telegram_client.sent_message_payloads == [
        (123, "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму».", None),
    ]
