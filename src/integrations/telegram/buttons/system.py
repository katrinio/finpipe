from src.integrations.telegram.buttons.navigation import NavigationButtons


class SystemButtons:
    WHOAMI = "👤 Кто я"
    CHATID = "/chatid"
    EASY_START = "❓ Как начать"


PUBLIC_COMMANDS = {
    SystemButtons.WHOAMI,
    NavigationButtons.HOME,
}
