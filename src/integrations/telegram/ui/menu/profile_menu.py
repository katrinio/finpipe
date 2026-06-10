from src.integrations.telegram.ui.buttons import MainMenuButtons, NavigationButtons, SettingsButtons, SignatureButtons


def build_profile_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SettingsButtons.DOWNLOAD_TEMPLATE},
                {"text": SettingsButtons.UPLOAD_TEMPLATE},
            ],
            [
                {"text": MainMenuButtons.SIGNATURE},
                {"text": NavigationButtons.BACK},
            ],
        ],
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
