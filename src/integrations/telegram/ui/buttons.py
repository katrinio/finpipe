# main menu
class MainMenuButtons:
    DOCUMENTS = "📄 Документы"
    INTEGRATIONS = "📧 Интеграции"
    PROFILE = "⚙️ Профиль"
    SYSTEM = "ℹ️ Система"


# documents
class DocumentsMenuButtons:
    INVOICE = "🧾 Invoice"
    BANK = "🏦 Банк PDF"
    TRANSFER_REQUEST = "💸 Запрос перевода"


# invoice
class InvoiceMenuButtons:
    SET_INVOICE_AMOUNT = "💰 Указать сумму"
    GET_INVOICE_AMOUNT = "💶 Текущая сумма"
    GENERATE_INVOICE = "📄 Сгенерировать Invoice"


# profile
class ProfileButtons:
    DOWNLOAD_TEMPLATE = "📥 Скачать шаблон профиля"
    UPLOAD_TEMPLATE = "📤 Загрузить шаблон профиля"
    MY_PROFILE = "👤 Мой профиль"
    SIGNATURE = "✍️ Подпись"


# signature
class SignatureButtons:
    SIGNATURE_UPLOAD = "📤 Загрузить"
    SIGNATURE_DELETE = "🗑 Удалить"
    SIGNATURE_STATUS = "📋 Статус"


# integrations
class IntegrationsButtons:
    GMAIL = "📧 Gmail"


# gmail
class GmailButtons:
    GMAIL_STATUS = "📊 Статус"
    GMAIL_CONNECT = "🔗 Подключить"
    GMAIL_DISCONNECT = "❌ Отключить"


# system
class SystemButtons:
    HELP = "📚 Помощь"
    HEALTHCHECK = "❤️ Healthcheck"
    ABOUT = "ℹ️ О проекте"
    WHOAMI = "👤 Кто я"
    STATUS = "📊 Статус профиля"


# navigation
class NavigationButtons:
    BACK = "⬅️ Назад"
    HOME = "🏠 Главное меню"


# owner
class OwnerButtons:
    ADD_USER = "/add_user"


PUBLIC_COMMANDS = {
    SystemButtons.WHOAMI,
}
