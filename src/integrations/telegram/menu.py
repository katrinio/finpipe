class MainMenuButtons:
    # Main menu
    DOCUMENTS = "📄 Документы"
    BANK = "🏦 Банк"
    SIGNATURE = "✍️ Подпись"
    GMAIL = "📧 Gmail"
    SYSTEM = "ℹ️ Система"

    # Signature menu
    SIGNATURE_STATUS = "📋 Статус"
    SIGNATURE_UPLOAD = "📤 Загрузить"
    SIGNATURE_DELETE = "🗑 Удалить"

    # Gmail menu
    GMAIL_STATUS = "📋 Статус"
    GMAIL_CONNECT = "🔗 Подключить"
    GMAIL_DISCONNECT = "🔌 Отключить"

    # Navigation
    BACK = "⬅️ Назад"
    HOME = "🏠 Главное меню"


class SystemButtons:
    HELP = "📚 Помощь"
    ABOUT = "ℹ️ О проекте"
    LAST_ACTION = "📝 Последнее действие"
    WHOAMI = "👤 Кто я"
    SYSTEM_STATUS = "🟢 Статус"
    HEALTHCHECK = "🌡 Healthcheck"


class NavigationButtons:
    BACK = "⬅️ Назад"


def build_main_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": "📄 Документы"},
                {"text": "🏦 Банк"},
            ],
            [
                {"text": "✍️ Подпись"},
                {"text": "📧 Gmail"},
            ],
            [
                {"text": "ℹ️ Система"},
            ],
        ],
        "resize_keyboard": True,
    }


def build_system_menu() -> dict:
    return {
        "keyboard": [
            [
                {"text": SystemButtons.HELP},
                {"text": SystemButtons.ABOUT},
            ],
            [
                {"text": SystemButtons.LAST_ACTION},
                {"text": SystemButtons.WHOAMI},
            ],
            [
                {"text": SystemButtons.SYSTEM_STATUS},
                {"text": SystemButtons.HEALTHCHECK},
            ],
            [
                {"text": NavigationButtons.BACK},
            ],
        ],
        "resize_keyboard": True,
    }
