from src.integrations.telegram.ui.buttons import DocumentsMenuButtons, NavigationButtons


def build_document_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": DocumentsMenuButtons.INVOICE},
                {"text": DocumentsMenuButtons.BANK},
            ],
            [
                {"text": NavigationButtons.BACK},
                {"text": DocumentsMenuButtons.TRANSFER_REQUEST},
            ],
        ],
        "resize_keyboard": True,
    }
