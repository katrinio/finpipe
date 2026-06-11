from src.integrations.telegram.ui.buttons import DocumentsMenuButtons, InvoiceMenuButtons, NavigationButtons


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


def build_invoice_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": InvoiceMenuButtons.SET_INVOICE_AMOUNT},
                {"text": InvoiceMenuButtons.GET_INVOICE_AMOUNT},
            ],
            [
                {"text": NavigationButtons.BACK},
                {"text": InvoiceMenuButtons.GENERATE_INVOICE},
            ],
        ],
        "resize_keyboard": True,
    }
