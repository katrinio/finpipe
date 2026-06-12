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
