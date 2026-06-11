class MainMenuButtons:
    # Main menu
    DOCUMENTS = "📄 Документы"
    INTEGRATIONS = "📧 Интеграции"
    PROFILE = "⚙️ Профиль"
    SYSTEM = "ℹ️ Система"


class DocumentsMenuButtons:
    INVOICE = "🧾 Invoice"
    BANK = "🏦 Банк PDF"
    TRANSFER_REQUEST = "💸 Запрос перевода"


class InvoiceMenuButtons:
    SET_INVOICE_AMOUNT = "💰 Указать сумму"
    GET_INVOICE_AMOUNT = "💶 Текущая сумма"
    GENERATE_INVOICE = "📄 Сгенерировать Invoice"


class ProfileButtons:
    DOWNLOAD_TEMPLATE = "📥 Скачать шаблон профиля"
    UPLOAD_TEMPLATE = "📤 Загрузить шаблон профиля"
    SIGNATURE = "✍️ Подпись"


class SignatureButtons:
    SIGNATURE_UPLOAD = "📤 Загрузить"
    SIGNATURE_DELETE = "🗑 Удалить"
    SIGNATURE_STATUS = "📋 Статус"


class IntegrationsButtons:
    GMAIL = "📧 Gmail"


class GmailButtons:
    GMAIL_STATUS = "📊 Статус"
    GMAIL_CONNECT = "🔗 Подключить"
    GMAIL_DISCONNECT = "❌ Отключить"


class SystemButtons:
    HELP = "📚 Помощь"
    HEALTHCHECK = "❤️ Healthcheck"
    ABOUT = "ℹ️ О проекте"
    WHOAMI = "👤 Кто я"
    STATUS = "📊 Статус профиля"


class NavigationButtons:
    BACK = "⬅️ Назад"
    HOME = "🏠 Главное меню"


class OwnerButtons:
    ADD_USER = "/add_user"


PUBLIC_COMMANDS = {
    SystemButtons.WHOAMI,
}
