from src.integrations.telegram.buttons.navigation import NavigationButtons


class SystemButtons:
    HELP = "📚 Помощь"
    HEALTHCHECK = "❤️ Healthcheck"
    ABOUT = "ℹ️ О проекте"
    WHOAMI = "👤 Кто я"
    STATUS = "📊 Статус профиля"


PUBLIC_COMMANDS = {
    SystemButtons.WHOAMI,
    NavigationButtons.HOME,
}
