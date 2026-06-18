from src.integrations.telegram.ui.buttons import GmailButtons, IntegrationsButtons, NavigationButtons


def build_integration_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": NavigationButtons.HOME},
                {"text": IntegrationsButtons.GMAIL},
            ],
        ],
        "resize_keyboard": True,
    }


def build_gmail_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": GmailButtons.GMAIL_CONNECT},
                {"text": GmailButtons.GMAIL_DISCONNECT},
            ],
            [
                {"text": GmailButtons.GMAIL_STATUS},
                {"text": GmailButtons.GMAIL_CLEAR_HISTORY},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
