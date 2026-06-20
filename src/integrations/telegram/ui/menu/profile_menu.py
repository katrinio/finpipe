from src.integrations.telegram.ui.buttons import NavigationButtons, ProfileButtons, SignatureButtons, SystemButtons


def build_profile_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": ProfileButtons.MY_PROFILE},
                {"text": SystemButtons.WHOAMI},
            ],
            [
                {"text": ProfileButtons.DOWNLOAD_TEMPLATE},
                {"text": ProfileButtons.UPLOAD_TEMPLATE},
            ],
            [
                {"text": SignatureButtons.SIGNATURE_UPLOAD},
                {"text": SignatureButtons.SIGNATURE_DELETE},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
