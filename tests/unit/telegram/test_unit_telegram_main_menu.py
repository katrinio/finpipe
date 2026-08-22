from typing import cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import NavigationButtons
from src.integrations.telegram.ui.menu.menu import build_main_menu
from tests.fakes.fake_telegram import FakeTelegramClient


def test_home_callback_opens_main_menu() -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(telegram=cast(TelegramClient, telegram_client), owner_telegram_id=123)

    bot.process_update(
        {
            "update_id": 11,
            "callback_query": {
                "data": NavigationButtons.HOME,
                "from": {"id": 123, "username": "alice"},
            },
        }
    )

    assert telegram_client.sent_message_payloads[-1] == (
        123,
        NavigationButtons.HOME,
        build_main_menu(),
    )


def test_legacy_main_menu_text_opens_main_menu() -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(telegram=cast(TelegramClient, telegram_client), owner_telegram_id=123)

    bot.handle_message("🏠 Главное меню", telegram_id=123, username="alice")

    assert telegram_client.sent_message_payloads[-1] == (
        123,
        NavigationButtons.HOME,
        build_main_menu(),
    )


def test_main_menu_has_no_multi_user_admin_controls() -> None:
    menu = build_main_menu()

    assert all(button["text"] != "🛠️ Админка" for row in menu["keyboard"] for button in row)
    assert menu["resize_keyboard"] is True
