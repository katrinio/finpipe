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
    WELCOME = "👋 Добро пожаловать в Finpipe!\nЛичный сервис для автоматизации документооборота.\n\n"

    ABOUT = (
        "🤖 Finpipe\n\n"
        "Личный сервис для автоматизации документооборота.\n\n"
        "Возможности:\n"
        "• Генерация документов по шаблонам\n"
        "• Заполнение банковских форм\n"
        "• Хранение данных компании и реквизитов\n"
        "• Шифрование и хранение электронной подписи\n"
        "• Интеграция с Gmail\n"
        "• Работа через Telegram\n\n"
        "Версия: 0.1"
    )
    HELP_HEADER = "📚 Доступные команды"
    WHOAMI_PREFIX = "👤 Информация о пользователе"

    PROJECT_RUNNING = "🟢 Finpipe работает."
    TELEGRAM_API_OK = "✅ Telegram API работает."

    ACCESS_DENIED = "⛔ У вас пока нет доступа к Finpipe.\nНажмите «Кто я» и отправьте свой Telegram ID владельцу бота."
    NO_SUCH_COMMAND = "🫥 Неизвестная команда."

    SYSTEM_ERROR = "💥 Произошла внутренняя ошибка."


class GmailMessages:
    GMAIL_CONNECTED = "✅ Gmail подключён."
    GMAIL_DISCONNECTED = "📧 Gmail отключён."
    GMAIL_NOT_CONNECTED = "🫥 Gmail не подключён."
    GMAIL_CONNECT_FAILED = "❌ Не удалось подключить Gmail.\nПопробуйте начать подключение заново."

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


class BankMessages:
    FILL_BANK_PDF = "⏳ Заполняется PDF от банка..."
    BANK_PDF_SENT = "✅ PDF банка отправлен."


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


class MenuMessages:
    MAIN_MENU = "🏠 Главное меню"

    DOCUMENTS = "📄 Документы"
    SIGNATURE = "✍️ Подпись"
    GMAIL = "📧 Gmail"

    SETTINGS = "⚙️ Настройки"
    STATUS = "ℹ️ Статус"


class BotInfo(CommonMessages, GmailMessages, SignatureMessages, InvoiceMessages, AuditLogMessages, MenuMessages, ProfileMessages, BankMessages):
    pass
