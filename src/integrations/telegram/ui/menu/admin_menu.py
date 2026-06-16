from src.integrations.telegram.ui.buttons import (
    NavigationButtons,
    OwnerButtons,
)


def build_admin_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": OwnerButtons.USERS},
            ],
            [
                {"text": OwnerButtons.STATISTICS},
                {"text": OwnerButtons.ERRORS},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }


def build_users_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": OwnerButtons.ADD_USER},
                {"text": OwnerButtons.REMOVE_USER},
            ],
            [
                {"text": OwnerButtons.LIST_USERS},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }


def build_add_user_confirmation_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": OwnerButtons.CONFIRM_ADD_USER},
                {"text": OwnerButtons.CANCEL_ADMIN_ACTION},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }


def build_remove_user_confirmation_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": OwnerButtons.CONFIRM_REMOVE_USER},
                {"text": OwnerButtons.CANCEL_ADMIN_ACTION},
            ],
            [
                {"text": NavigationButtons.HOME},
            ],
        ],
        "resize_keyboard": True,
    }
