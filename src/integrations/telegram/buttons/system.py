from src.integrations.telegram.buttons.navigation import NavigationButtons


class SystemButtons:
    WHOAMI = "👤 Кто я"
    CHATID = "/chatid"
    EASY_START = "❓ Как начать"

    CB_WHOAMI = "nav:whoami"
    CB_EASY_START = "nav:easy_start"
    CB_BACK = "nav:main"


PUBLIC_COMMANDS = {
    SystemButtons.WHOAMI,
    NavigationButtons.HOME,
}
