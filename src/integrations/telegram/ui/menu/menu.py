from src.integrations.telegram.ui.buttons import MainMenuButtons


def build_main_menu() -> dict:
    """Строит главное меню владельца."""

    keyboard = [
        [
            {"text": MainMenuButtons.DOCUMENTS},
            {"text": MainMenuButtons.PROFILE},
        ],
        [{"text": MainMenuButtons.SYSTEM}],
    ]

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
    }
