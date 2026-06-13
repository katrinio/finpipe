from enum import Enum


class UserState(Enum):
    WAITING_SIGNATURE_UPLOAD = "waiting_signature_upload"
    WAITING_PROFILE_TEMPLATE_UPLOAD = "waiting_profile_template_upload"
    WAITING_INVOICE_AMOUNT = "waiting_invoice_amount"
    WAITING_CONVERSION_AMOUNT = "waiting_conversion_amount"
    WAITING_NEW_USER_ID = "waiting_new_user_id"
    WAITING_NEW_USER_CONFIRMATION = "waiting_new_user_confirmation"
    WAIT_CONFIRM_ADD_USER = "wait_confirm_add_user"
    WAITING_REMOVE_USER_ID = "waiting_remove_user_id"
    WAIT_CONFIRM_REMOVE_USER = "wait_confirm_remove_user"
