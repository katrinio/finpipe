from src.integrations.telegram.commands import format_whoami
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu


def test_guest_menu_contains_only_whoami() -> None:
    menu = build_guest_menu()
    all_buttons = [btn for row in menu["inline_keyboard"] for btn in row]
    assert len(all_buttons) == 1
    assert all_buttons[0]["callback_data"] == "nav:whoami"


def test_format_whoami_uses_friendly_labels() -> None:
    assert format_whoami(123456789, "username") == ("👤 Информация о пользователе\nTelegram ID: 123456789\nUsername: @username")
