from enum import Enum


class UserState(Enum):
    WAITING_SIGNATURE_UPLOAD = "waiting_signature_upload"
    WAITING_PROFILE_TEMPLATE_UPLOAD = "waiting_profile_template_upload"
    WAITING_INVOICE_AMOUNT = "waiting_invoice_amount"
