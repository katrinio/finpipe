from src.integrations.telegram.ui.buttons import DocumentsMenuButtons, InvoiceMenuButtons, NavigationButtons


def build_document_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": DocumentsMenuButtons.SALARY_INVOICE},
                {"text": DocumentsMenuButtons.BANK_CONFIRMATION},
            ],
            [
                {"text": NavigationButtons.HOME},
                {"text": DocumentsMenuButtons.CONVERSION_ORDER},
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
                {"text": NavigationButtons.HOME},
                {"text": InvoiceMenuButtons.GENERATE_INVOICE},
            ],
        ],
        "resize_keyboard": True,
    }
