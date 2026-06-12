from enum import Enum


class UserState(Enum):
    WAITING_SIGNATURE_UPLOAD = "waiting_signature_upload"
    WAITING_PROFILE_TEMPLATE_UPLOAD = "waiting_profile_template_upload"
    WAITING_INVOICE_AMOUNT = "waiting_invoice_amount"
    WAITING_NEW_USER_ID = "waiting_new_user_id"
    WAITING_NEW_USER_CONFIRMATION = "waiting_new_user_confirmation"
    WAITING_REMOVE_USER_ID = "waiting_remove_user_id"
