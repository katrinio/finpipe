from src.integrations.telegram.commands import format_whoami
from src.integrations.telegram.ui.menu.guest_menu import build_guest_menu


def test_guest_menu_contains_only_whoami() -> None:
    assert build_guest_menu() == {
        "keyboard": [[{"text": "👤 Кто я"}]],
        "resize_keyboard": True,
    }


def test_format_whoami_uses_friendly_labels() -> None:
    assert format_whoami(123456789, "username") == ("👤 Информация о пользователе\nTelegram ID: 123456789\nUsername: @username")
