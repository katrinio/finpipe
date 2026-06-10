"""
Правила использования эмодзи в сообщениях Telegram-бота.

Статусы:
✅ Успешное выполнение
❌ Ошибка
💥 Системная ошибка
⚠️ Предупреждение
⏳ Выполняется операция
🫥 Объект не найден
ℹ️ Информационное сообщение

Остальные эмодзи обозначают предметную область
(📧 Gmail, ✍️ Подпись, 📄 Документы, 📝 Аудит и т.д.)
и не должны использоваться как индикаторы статуса.
"""


class CommonMessages:
    ABOUT = "🤖 Finpipe MVP\n\nFeatures:\n• Invoice generation\n• Gmail integration\n• Telegram bot\n• SQLite storage\n\nVersion: 0.1"

    HELP_HEADER = "📚 Доступные команды"
    WHOAMI_PREFIX = "👤 Вы"

    PROJECT_RUNNING = "🟢 Finpipe работает."
    TELEGRAM_API_OK = "✅ Telegram API работает."

    ACCESS_DENIED = "⛔ Доступ запрещён."
    NO_SUCH_COMMAND = "🫥 Неизвестная команда."

    SYSTEM_ERROR = "💥 Произошла внутренняя ошибка."


class GmailMessages:
    GMAIL_CONNECTED = "✅ Gmail подключён."
    GMAIL_DISCONNECTED = "📧 Gmail отключён."
    GMAIL_NOT_CONNECTED = "🫥 Gmail не подключён."

    GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE = "⚠️ Подключение Gmail временно недоступно."


class SignatureMessages:
    # status
    SIGNATURE_FOUND = "✅ Подпись загружена."
    SIGNATURE_NOT_FOUND = "🫥 Подпись не найдена."

    # upload
    SIGNATURE_REQUIREMENTS = "✍️ Пришлите подпись в PNG формате.\n\nТребования:\n- PNG\n- до 2 МБ\n- прозрачный фон рекомендуется"

    SIGNATURE_UPDATED = "✅ Подпись успешно обновлена."

    # validation errors
    SIGNATURE_NOT_PNG = "❌ Разрешены только PNG файлы."
    SIGNATURE_TOO_LARGE = "❌ Размер файла превышает 2 МБ."
    SIGNATURE_UPLOAD_ERROR = "❌ Не удалось обработать изображение."

    # delete
    SIGNATURE_DELETED = "🗑️ Подпись удалена."


class InvoiceMessages:
    GENERATING_INVOICE = "⏳ Формируется инвойс..."
    INVOICE_SENT = "✅ Инвойс отправлен."


class AuditLogMessages:
    NO_AUDIT_LOG_RECORDS = "📝 Записи аудита отсутствуют."


class ProfileMessages:
    PROFILE_TEMPLATE_SENT = "📥 Шаблон профиля отправлен.\nЗаполните файл и загрузите его обратно."
    PROFILE_TEMPLATE_REQUIREMENTS = (
        "✍️ Пришлите заполненный шаблон в YAML формате.\n\nТребования:\n- YAML\n- до 2 МБ\n- заполнен словарем значений по ключам шаблона"
    )

    PROFILE_TEMPLATE_UPDATED = "✅ Данные пользователя успешно обновлены."

    # validation errors
    PROFILE_TEMPLATE_NOT_YAML = "❌ Разрешены только YAML файлы."
    PROFILE_TEMPLATE_TOO_LARGE = "❌ Размер файла превышает 2 МБ."
    PROFILE_TEMPLATE_UPLOAD_ERROR = "❌ Не удалось обработать изображение."


class MenuMessages:
    MAIN_MENU = "🏠 Главное меню"

    DOCUMENTS = "📄 Документы"
    SIGNATURE = "✍️ Подпись"
    GMAIL = "📧 Gmail"

    SETTINGS = "⚙️ Настройки"
    STATUS = "ℹ️ Статус"


class BotInfo(CommonMessages, GmailMessages, SignatureMessages, InvoiceMessages, AuditLogMessages, MenuMessages, ProfileMessages):
    pass
