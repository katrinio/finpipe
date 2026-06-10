from src.integrations.telegram.ui.buttons import GmailButtons, MainMenuButtons, NavigationButtons


def build_integration_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": NavigationButtons.BACK},
                {"text": MainMenuButtons.GMAIL},
            ],
        ],
        "resize_keyboard": True,
    }


def build_gmail_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": GmailButtons.GMAIL_DISCONNECT},
                {"text": GmailButtons.GMAIL_CONNECT},
            ],
            [
                {"text": NavigationButtons.BACK},
                {"text": GmailButtons.GMAIL_STATUS},
            ],
        ],
        "resize_keyboard": True,
    }
