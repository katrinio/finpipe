from src.integrations.telegram.ui.buttons import SystemButtons


def build_guest_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SystemButtons.WHOAMI},
            ],
        ],
        "resize_keyboard": True,
    }
