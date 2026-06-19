from src.integrations.telegram.ui.buttons import (
    BankDayButtons,
    DocumentsMenuButtons,
    InvoiceMenuButtons,
    NavigationButtons,
)


def build_invoice_send_prompt_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": InvoiceMenuButtons.SEND_TO_COMPANY, "callback_data": InvoiceMenuButtons.SEND_TO_COMPANY},
                {"text": InvoiceMenuButtons.SKIP_SEND, "callback_data": InvoiceMenuButtons.SKIP_SEND},
            ],
        ],
    }


def build_bank_day_reply_prompt_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": BankDayButtons.REPLY_TO_BANK, "callback_data": BankDayButtons.REPLY_TO_BANK},
                {"text": BankDayButtons.SKIP_REPLY, "callback_data": BankDayButtons.SKIP_REPLY},
            ],
        ],
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
