from src.integrations.telegram.ui.buttons import MainMenuButtons, OwnerButtons


def build_main_menu(is_owner: bool = False) -> dict:
    """Строит главное меню с учётом owner-доступа."""

    keyboard = [
        [
            {"text": MainMenuButtons.DOCUMENTS, "callback_data": MainMenuButtons.CB_DOCUMENTS},
            {"text": MainMenuButtons.PROFILE, "callback_data": MainMenuButtons.CB_PROFILE},
        ],
        [
            {"text": MainMenuButtons.INTEGRATIONS, "callback_data": MainMenuButtons.CB_INTEGRATIONS},
            {"text": MainMenuButtons.SYSTEM, "callback_data": MainMenuButtons.CB_SYSTEM},
        ],
    ]

    if is_owner:
        keyboard.append([{"text": OwnerButtons.ADMIN_PANEL, "callback_data": MainMenuButtons.CB_ADMIN}])

    return {"inline_keyboard": keyboard}
