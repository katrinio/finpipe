from src.integrations.telegram.ui.buttons import ProfileButtons, SignatureButtons


def build_profile_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": ProfileButtons.MY_PROFILE, "callback_data": ProfileButtons.CB_VIEW},
            ],
            [
                {"text": ProfileButtons.DOWNLOAD_TEMPLATE, "callback_data": ProfileButtons.CB_DOWNLOAD_TEMPLATE},
                {"text": ProfileButtons.UPLOAD_TEMPLATE, "callback_data": ProfileButtons.CB_UPLOAD_TEMPLATE},
            ],
            [
                {"text": SignatureButtons.SIGNATURE_UPLOAD, "callback_data": SignatureButtons.CB_UPLOAD},
                {"text": SignatureButtons.SIGNATURE_DELETE, "callback_data": SignatureButtons.CB_DELETE},
            ],
            [
                {"text": "◀️ Назад", "callback_data": ProfileButtons.CB_BACK},
            ],
        ],
    }
