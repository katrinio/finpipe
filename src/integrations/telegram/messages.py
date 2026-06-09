class CommonMessages:
    ABOUT = "🤖 Finpipe MVP\n\nFeatures:\n• Invoice generation\n• Gmail integration\n• Telegram bot\n• SQLite storage\n\nVersion: 0.1"

    ACCESS_DENIED = "⛔ Доступ запрещён"
    NO_SUCH_COMMAND = "🫥 Неизвестная команда"
    PROJECT_RUNNING = "🟢 Finpipe работает."
    TELEGRAM_API_OK = "✅ Telegram API работает."
    HELP_HEADER = "📚 Доступные команды"
    WHOAMI_PREFIX = "👤 Вы"


class GmailMessages:
    GMAIL_NOT_CONNECTED = "❌ Gmail не подключён."
    GMAIL_CONNECTED = "✅ Gmail подключён."
    GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE = "⚠️ Подключение Gmail временно недоступно."


class SignatureMessages:
    SIGNATURE_NOT_FOUND = "❌ Подпись не найдена."
    SIGNATURE_FOUND = "✅ Подпись загружена."
    SIGNATURE_DELETED = "🗑 Подпись удалена."
    SIGNATURE_UPDATED = "✅ Подпись обновлена."


class InvoiceMessages:
    GENERATING_INVOICE = "⏳ Формируется инвойс..."
    INVOICE_SENT = "✅ Инвойс отправлен."


class AuditLogMessages:
    NO_AUDIT_LOG_RECORDS = "📝 Записи аудита отсутствуют."


class MenuMessages:
    MAIN_MENU = "🏠 Главное меню"
    DOCUMENTS = "📄 Документы"
    SIGNATURE = "✍️ Подпись"
    GMAIL = "📧 Gmail"
    SETTINGS = "⚙️ Настройки"
    STATUS = "ℹ️ Статус"


class BotInfo(
    CommonMessages,
    GmailMessages,
    SignatureMessages,
    InvoiceMessages,
    AuditLogMessages,
    MenuMessages,
):
    pass
