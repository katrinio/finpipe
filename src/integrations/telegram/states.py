from enum import Enum


class UserState(Enum):
    WAITING_SIGNATURE_UPLOAD = "waiting_signature_upload"
    WAITING_PROFILE_TEMPLATE_UPLOAD = "waiting_profile_template_upload"
    WAITING_BANK_DOCUMENT_UPLOAD = "waiting_bank_document_upload"
    WAITING_INVOICE_AMOUNT = "waiting_invoice_amount"
