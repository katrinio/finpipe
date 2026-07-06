from src.integrations.telegram.ui.buttons import (
    BankDayButtons,
    DocumentsMenuButtons,
    InvoiceMenuButtons,
    NavigationButtons,
)


def build_invoice_send_prompt_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": InvoiceMenuButtons.SEND_TO_COMPANY},
                {"text": NavigationButtons.SKIP},
            ],
        ],
        "resize_keyboard": True,
    }


def build_bank_day_reply_prompt_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": BankDayButtons.REPLY_TO_BANK},
                {"text": NavigationButtons.SKIP},
            ],
        ],
        "resize_keyboard": True,
    }


def build_bank_day_start_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": BankDayButtons.START},
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }


def build_document_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": DocumentsMenuButtons.SALARY_INVOICE},
                {"text": DocumentsMenuButtons.BANK_DAY},
            ],
            [
                {"text": BankDayButtons.REQUEST_CONVERSION},
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
