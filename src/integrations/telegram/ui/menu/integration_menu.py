from src.integrations.telegram.ui.buttons import GmailButtons, NavigationButtons


def build_gmail_clear_history_confirm_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": GmailButtons.GMAIL_CLEAR_HISTORY_CONFIRM},
                {"text": NavigationButtons.SKIP},
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
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
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
            [
                {"text": GmailButtons.GMAIL_CLEAR_HISTORY},
            ],
        ],
        "resize_keyboard": True,
    }
