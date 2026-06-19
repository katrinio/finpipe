from src.integrations.telegram.ui.buttons import (
    BankDayButtons,
    DocumentsMenuButtons,
    InvoiceMenuButtons,
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


def build_bank_day_start_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": BankDayButtons.START, "callback_data": DocumentsMenuButtons.CB_BANK_DAY_START},
                {"text": "◀️ Назад", "callback_data": DocumentsMenuButtons.CB_BACK},
            ],
        ],
    }


def build_document_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": DocumentsMenuButtons.SALARY_INVOICE, "callback_data": DocumentsMenuButtons.CB_INVOICE},
                {"text": DocumentsMenuButtons.BANK_DAY, "callback_data": DocumentsMenuButtons.CB_BANK_DAY_INFO},
            ],
            [
                {"text": "◀️ Назад", "callback_data": DocumentsMenuButtons.CB_BACK},
            ],
        ],
    }


def build_invoice_menu() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": InvoiceMenuButtons.SET_INVOICE_AMOUNT, "callback_data": InvoiceMenuButtons.CB_SET_AMOUNT},
                {"text": InvoiceMenuButtons.GET_INVOICE_AMOUNT, "callback_data": InvoiceMenuButtons.CB_GET_AMOUNT},
            ],
            [
                {"text": InvoiceMenuButtons.GENERATE_INVOICE, "callback_data": InvoiceMenuButtons.CB_GENERATE},
            ],
            [
                {"text": "◀️ Назад", "callback_data": InvoiceMenuButtons.CB_BACK},
            ],
        ],
    }
