from src.integrations.telegram.ui.buttons import GmailButtons, MainMenuButtons, NavigationButtons, SettingsButtons, SignatureButtons, SystemButtons


def build_main_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": MainMenuButtons.DOCUMENTS},
                {"text": MainMenuButtons.PROFILE},
            ],
            [
                {"text": MainMenuButtons.INTEGRATIONS},
                {"text": MainMenuButtons.SYSTEM},
            ],
        ],
        "resize_keyboard": True,
    }


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


def build_system_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SystemButtons.ABOUT},
                {"text": SystemButtons.HEALTHCHECK},
            ],
            [
                {"text": NavigationButtons.BACK},
                {"text": SystemButtons.WHOAMI},
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


def build_signature_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SignatureButtons.SIGNATURE_DELETE},
                {"text": SignatureButtons.SIGNATURE_UPLOAD},
            ],
            [
                {"text": NavigationButtons.BACK},
                {"text": SignatureButtons.SIGNATURE_STATUS},
            ],
        ],
        "resize_keyboard": True,
    }


def build_settings_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SettingsButtons.DOWNLOAD_TEMPLATE},
                {"text": SettingsButtons.UPLOAD_TEMPLATE},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
    }
