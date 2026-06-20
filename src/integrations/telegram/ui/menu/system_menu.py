from src.integrations.telegram.ui.buttons import NavigationButtons, OwnerButtons, SystemButtons


def build_system_menu(is_owner: bool = False) -> dict:
    keyboard = [
        [
            {"text": SystemButtons.EASY_START},
        ],
        [
            {"text": NavigationButtons.HOME},
        ],
    ]

    if is_owner:
        keyboard.append([{"text": OwnerButtons.ADMIN_PANEL}])

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
    }
