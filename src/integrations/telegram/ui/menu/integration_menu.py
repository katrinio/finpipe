from src.integrations.telegram.ui.buttons import GmailButtons, NavigationButtons


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
