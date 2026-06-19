from src.integrations.telegram.ui.buttons import SystemButtons


def build_guest_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": SystemButtons.WHOAMI, "callback_data": SystemButtons.CB_WHOAMI},
            ],
        ],
    }
