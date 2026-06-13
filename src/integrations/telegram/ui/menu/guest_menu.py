from src.integrations.telegram.ui.buttons import NavigationButtons, SystemButtons


def build_guest_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SystemButtons.WHOAMI},
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
