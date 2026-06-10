from src.integrations.telegram.ui.buttons import MainMenuButtons


def build_main_menu() -> dict:
    return {
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
