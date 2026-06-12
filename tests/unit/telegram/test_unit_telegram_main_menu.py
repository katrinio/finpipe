from src.integrations.telegram.ui.buttons import MainMenuButtons, OwnerButtons
from src.integrations.telegram.ui.menu.menu import build_main_menu


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
