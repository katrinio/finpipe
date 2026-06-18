from src.integrations.telegram.buttons.navigation import NavigationButtons


class SystemButtons:
    HELP = "📚 Помощь"
    ABOUT = "ℹ️ О проекте"
    WHOAMI = "👤 Кто я"
    CHATID = "/chatid"
    EASY_START = "🚀 Начало работы"


PUBLIC_COMMANDS = {
    SystemButtons.WHOAMI,
    NavigationButtons.HOME,
}
