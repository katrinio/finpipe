from typing import cast

from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import MainMenuButtons, NavigationButtons, OwnerButtons
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.storage.dependencies import StorageDependencies
from tests.fakes.fake_storage import FakeStorage
from tests.fakes.fake_telegram import FakeTelegramClient


def test_home_callback_opens_main_menu() -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({123})), telegram=cast(TelegramClient, telegram_client))

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
        build_main_menu(is_owner=True),
    )


def test_legacy_main_menu_text_opens_main_menu() -> None:
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(cast(StorageDependencies, FakeStorage({123})), telegram=cast(TelegramClient, telegram_client))

    bot.handle_message("🏠 Главное меню", telegram_id=123, username="alice")

    assert telegram_client.sent_message_payloads[-1] == (
        123,
        NavigationButtons.HOME,
        build_main_menu(is_owner=True),
    )


def test_main_menu_shows_admin_button_for_owner() -> None:
    menu = build_main_menu(is_owner=True)

    assert menu == {
        "keyboard": [
            [
                {"text": MainMenuButtons.DOCUMENTS},
                {"text": MainMenuButtons.PROFILE},
            ],
            [
                {"text": MainMenuButtons.INTEGRATIONS},
                {"text": MainMenuButtons.SYSTEM},
            ],
            [
                {"text": OwnerButtons.ADMIN_PANEL},
            ],
        ],
        "resize_keyboard": True,
    }


def test_main_menu_hides_admin_button_for_regular_user() -> None:
    menu = build_main_menu(is_owner=False)

    assert menu == {
        "keyboard": [
            [
                {"text": MainMenuButtons.DOCUMENTS},
                {"text": MainMenuButtons.PROFILE},
            ],
            [
                {"text": MainMenuButtons.INTEGRATIONS},
                {"text": MainMenuButtons.SYSTEM},
            ],
        ],
        "resize_keyboard": True,
    }
