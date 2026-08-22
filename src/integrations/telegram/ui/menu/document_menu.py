from src.integrations.telegram.buttons import (
    DocumentsMenuButtons,
    InvoiceMenuButtons,
    NavigationButtons,
)


def build_document_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": DocumentsMenuButtons.SALARY_INVOICE},
                {"text": DocumentsMenuButtons.CONVERSION_REQUEST},
            ],
            [
                {"text": DocumentsMenuButtons.BANK_TRANSFER_CONFIRMATION},
            ],
            [
                {"text": NavigationButtons.HOME},
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
                {"text": InvoiceMenuButtons.GENERATE_INVOICE},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
