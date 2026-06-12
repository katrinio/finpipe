from src.integrations.telegram.ui.buttons import NavigationButtons, OwnerButtons, SystemButtons


def build_system_menu(is_owner: bool = False) -> dict:
    keyboard = [
        [
            {"text": SystemButtons.ABOUT},
            {"text": SystemButtons.HEALTHCHECK},
        ],
        [
            {"text": SystemButtons.STATUS},
            {"text": SystemButtons.WHOAMI},
        ],
        [
            {"text": NavigationButtons.BACK},
        ],
    ]

    if is_owner:
        keyboard.append([{"text": OwnerButtons.ADMIN_PANEL}])

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
    }
