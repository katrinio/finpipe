from src.integrations.telegram.bot import TelegramBot
from src.integrations.telegram.ui.buttons import DocumentsMenuButtons, GmailButtons, MainMenuButtons, OwnerButtons
from src.integrations.telegram.ui.menu.menu import build_main_menu
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from tests.fakes.fake_telegram import FakeTelegramClient


def test_back_button_from_documents_opens_main_menu() -> None:
    build_storage_dependencies()
    AllowedUser.create(123, "alice")
    telegram_client = FakeTelegramClient()
    bot = TelegramBot(build_storage_dependencies(), telegram=telegram_client)

    bot.process_update(
        {
            "update_id": 11,
            "callback_query": {
                "id": "cq1",
                "data": DocumentsMenuButtons.CB_BACK,
                "from": {"id": 123, "username": "alice"},
                "message": {"message_id": 1, "chat": {"id": 123}},
            },
        }
    )

    assert telegram_client.sent_message_payloads[-1][2] == build_main_menu(is_owner=False)


def test_main_menu_shows_admin_button_for_owner() -> None:
    menu = build_main_menu(is_owner=True)

    all_buttons = [btn for row in menu["inline_keyboard"] for btn in row]
    assert any(btn["text"] == OwnerButtons.ADMIN_PANEL for btn in all_buttons)
    assert any(btn["callback_data"] == MainMenuButtons.CB_ADMIN for btn in all_buttons)


def test_main_menu_hides_admin_button_for_regular_user() -> None:
    menu = build_main_menu(is_owner=False)

    all_buttons = [btn for row in menu["inline_keyboard"] for btn in row]
    assert all(btn["text"] != OwnerButtons.ADMIN_PANEL for btn in all_buttons)


def test_main_menu_nav_callbacks_present() -> None:
    menu = build_main_menu(is_owner=False)

    callback_data_values = {btn["callback_data"] for row in menu["inline_keyboard"] for btn in row}
    assert MainMenuButtons.CB_DOCUMENTS in callback_data_values
    assert MainMenuButtons.CB_PROFILE in callback_data_values
    assert GmailButtons.CB_GMAIL in callback_data_values
    assert MainMenuButtons.CB_SYSTEM in callback_data_values
