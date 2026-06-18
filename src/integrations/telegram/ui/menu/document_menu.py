from src.integrations.telegram.ui.buttons import (
    DocumentsMenuButtons,
    InvoiceMenuButtons,
    NavigationButtons,
)


def build_invoice_send_prompt_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": InvoiceMenuButtons.SEND_TO_COMPANY},
                {"text": InvoiceMenuButtons.SKIP_SEND},
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def build_document_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": DocumentsMenuButtons.SALARY_INVOICE},
                {"text": DocumentsMenuButtons.BANK_DAY},
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
                {"text": NavigationButtons.HOME},
                {"text": InvoiceMenuButtons.GENERATE_INVOICE},
            ],
        ],
        "resize_keyboard": True,
    }
