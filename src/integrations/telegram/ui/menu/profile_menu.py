from src.integrations.telegram.ui.buttons import NavigationButtons, ProfileButtons, SignatureButtons


def build_profile_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": ProfileButtons.DOWNLOAD_TEMPLATE},
                {"text": ProfileButtons.UPLOAD_TEMPLATE},
            ],
            [
                {"text": ProfileButtons.SIGNATURE},
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
