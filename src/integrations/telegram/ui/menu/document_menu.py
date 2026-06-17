from src.integrations.telegram.ui.buttons import (
    BankConfirmationButtons,
    ConversionOrderButtons,
    DocumentsMenuButtons,
    InvoiceMenuButtons,
    NavigationButtons,
)


def build_document_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": DocumentsMenuButtons.SALARY_INVOICE},
                {"text": DocumentsMenuButtons.BANK_CONFIRMATION},
            ],
            [
                {"text": DocumentsMenuButtons.CONVERSION_ORDER},
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }


def build_bank_confirmation_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": BankConfirmationButtons.UPLOAD_FOR_FILLING},
                {"text": BankConfirmationButtons.CHECK_BANK_EMAIL},
            ],
            [
                {"text": BankConfirmationButtons.GET_AND_PROCESS},
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


def build_conversion_order_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": ConversionOrderButtons.SET_AMOUNT},
                {"text": ConversionOrderButtons.GET_AMOUNT},
            ],
            [
                {"text": ConversionOrderButtons.USE_BANK_AMOUNT},
                {"text": ConversionOrderButtons.GENERATE},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
