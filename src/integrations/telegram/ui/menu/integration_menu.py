from src.integrations.telegram.ui.buttons import GmailButtons, IntegrationsButtons, NavigationButtons


def build_integration_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": IntegrationsButtons.GMAIL, "callback_data": IntegrationsButtons.CB_GMAIL},
            ],
            [
                {"text": NavigationButtons.BACK, "callback_data": IntegrationsButtons.CB_BACK},
            ],
        ],
    }


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
