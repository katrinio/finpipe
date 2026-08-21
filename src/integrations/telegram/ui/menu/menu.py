from src.integrations.telegram.ui.buttons import MainMenuButtons, OwnerButtons


def build_main_menu(is_owner: bool = False) -> dict:
    """Строит главное меню с учётом owner-доступа."""

    keyboard = [
        [
            {"text": MainMenuButtons.DOCUMENTS},
            {"text": MainMenuButtons.PROFILE},
        ],
        [{"text": MainMenuButtons.SYSTEM}],
    ]

    if is_owner:
        keyboard.append([{"text": OwnerButtons.ADMIN_PANEL}])

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
    }
