from src.integrations.telegram.ui.buttons import NavigationButtons, SystemButtons


def build_system_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SystemButtons.ABOUT},
                {"text": SystemButtons.HEALTHCHECK},
            ],
            [
                {"text": SystemButtons.STATUS},
                {"text": SystemButtons.WHOAMI},
            ],
            [
                {"text": NavigationButtons.BACK},
            ],
        ],
        "resize_keyboard": True,
    }
