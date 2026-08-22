from src.integrations.telegram.ui.buttons import NavigationButtons, SystemButtons


def build_system_menu() -> dict:
    keyboard = [
        [
            {"text": SystemButtons.EASY_START},
            {"text": SystemButtons.READINESS},
        ],
        [
            {"text": NavigationButtons.HOME},
        ],
    ]

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
    }
