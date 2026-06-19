from src.integrations.telegram.ui.buttons import GmailButtons, NavigationButtons


def build_gmail_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": GmailButtons.GMAIL_CONNECT, "callback_data": GmailButtons.CB_CONNECT},
                {"text": GmailButtons.GMAIL_DISCONNECT, "callback_data": GmailButtons.CB_DISCONNECT},
            ],
            [
                {"text": GmailButtons.GMAIL_STATUS, "callback_data": GmailButtons.CB_STATUS},
                {"text": GmailButtons.GMAIL_CLEAR_HISTORY, "callback_data": GmailButtons.CB_CLEAR_HISTORY},
            ],
            [
                {"text": NavigationButtons.BACK, "callback_data": GmailButtons.CB_BACK},
            ],
        ],
    }
