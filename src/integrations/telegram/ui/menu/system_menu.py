from src.integrations.telegram.ui.buttons import NavigationButtons, SystemButtons


def build_system_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SystemButtons.ABOUT},
                {"text": SystemButtons.HEALTHCHECK},
            ],
            [
                {"text": NavigationButtons.BACK},
                {"text": SystemButtons.WHOAMI},
            ],
        ],
        "resize_keyboard": True,
    }
