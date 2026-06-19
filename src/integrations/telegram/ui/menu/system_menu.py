from src.integrations.telegram.ui.buttons import MainMenuButtons, OwnerButtons, SystemButtons


def build_system_menu(is_owner: bool = False) -> dict:
    keyboard = [
        [
            {"text": SystemButtons.EASY_START, "callback_data": SystemButtons.CB_EASY_START},
            {"text": SystemButtons.WHOAMI, "callback_data": SystemButtons.CB_WHOAMI},
        ],
        [
            {"text": "◀️ Назад", "callback_data": SystemButtons.CB_BACK},
        ],
    ]

    if is_owner:
        keyboard.append([{"text": OwnerButtons.ADMIN_PANEL, "callback_data": MainMenuButtons.CB_ADMIN}])

    return {"inline_keyboard": keyboard}
