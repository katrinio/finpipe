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


class Msg:
    @staticmethod
    def success(text: str) -> str:
        return f"✅ {text}"

    @staticmethod
    def error(text: str) -> str:
        return f"❌ {text}"

    @staticmethod
    def warning(text: str) -> str:
        return f"⚠️ {text}"


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

    USE_CONFIRMATION_BTN = "Используйте кнопки подтверждения ниже."


class GmailMessages:
    GMAIL_CONNECTED = "✅ Gmail подключён."
    GMAIL_DISCONNECTED = "📧 Gmail отключён."
    GMAIL_NOT_CONNECTED = "🫥 Gmail не подключён."
    GMAIL_CONNECT_PROMPT = "📧 Gmail\n\nПодключите аккаунт Google для работы с банковыми письмами.\n\nНажмите кнопку ниже для авторизации."
    # TODO(vps): уточнить production-сообщения Gmail OAuth с учётом постоянного домена и поддержки пользователя.
    GMAIL_CONNECT_FAILED = "❌ Не удалось подключить Gmail.\nПопробуйте начать подключение заново."

    GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE = "⚠️ Подключение Gmail временно недоступно."


class SignatureMessagesV2:
    class Status:
        FOUND = Msg.success("Подпись загружена.")
        NOT_FOUND = Msg.warning("Подпись не найдена.")

    class Upload:
        REQUIREMENTS = "✍️ Пришлите подпись в PNG формате.\n\nТребования:\n- PNG\n- до 2 МБ\n- прозрачный фон рекомендуется"
        UPDATED = Msg.success("Подпись успешно обновлена.")

    class Validation:
        NOT_PNG = Msg.error("Разрешены только PNG файлы.")
        TOO_LARGE = Msg.error("Размер файла превышает 2 МБ")
        UPLOAD_ERROR = Msg.error("Не удалось обработать изображение.")

    class Delete:
        DELETED = "🗑️ Подпись удалена."


class InvoiceMessages:
    GENERATING_INVOICE = "⏳ Формируется Salary Invoice..."
    INVOICE_SENT = "✅ Salary Invoice отправлен."
    NO_INVOICE_AMOUNT = "💰 Сумма Salary Invoice не задана.\nИспользуйте «Указать сумму»."
    AMOUNT_SAVED = "✅ Сумма Salary Invoice сохранена: {0} EUR"
    INPUT_INVOICE_AMOUNT = "💰 Введите сумму Salary Invoice:"

    # validation errors
    INVOICE_AMOUNT_NOT_INT = "❌ Сумма должна содержать только цифры.\nПример: 1500"


class BankMessages:
    GENERATING_BANK_CONFIRMATION = "⏳ Формируется подтверждение для банка..."
    BANK_CONFIRMATION_SENT = "✅ Подтверждение для банка отправлено."


class ConversionOrderMessages:
    NO_EXCHANGE_AMOUNT = "❌ Сумма к обмену не определена.\nСначала обработайте банковский PDF, чтобы сохранить полученную сумму."


class AuditLogMessages:
    NO_AUDIT_LOG_RECORDS = "📝 Записи аудита отсутствуют."


class ProfileMessageV2:
    class Status:
        FOUND = Msg.success("Подпись загружена.")
        NOT_FOUND = Msg.warning("Подпись не найдена.")

    class Upload:
        REQUIREMENTS = (
            "✍️ Пришлите заполненный шаблон в YAML формате.\n\nТребования:\n- YAML\n- до 2 МБ\n- заполнен словарем значений по ключам шаблона"
        )
        TEMPLATE_SENT = "📥 Шаблон профиля отправлен.\nЗаполните файл и загрузите его обратно."
        UPDATED = Msg.success("Данные пользователя успешно обновлены.")
        UPLOADED = Msg.success("Профиль успешно загружен.\nКомпания: {0}\nБанк: {1}")

    class Validation:
        NOT_YAML = Msg.error("Разрешены только YAML файлы.")
        TOO_LARGE = Msg.error("Размер файла превышает 2 МБ.")


class MenuMessages:
    MAIN_MENU = "🏠 Главное меню"

    DOCUMENTS = "📄 Документы"
    SIGNATURE = "✍️ Подпись"
    GMAIL = "📧 Gmail"

    SETTINGS = "⚙️ Настройки"
    STATUS = "ℹ️ Статус"


class OwnerMessages:
    INPUT_USER_ID = "Введите Telegram ID пользователя, который уже открыл бота."
    INPUT_USER_ID_TO_REVOKE = "Введите Telegram ID пользователя, у которого нужно отозвать доступ."
    USER_TO_ADD_IS_FOUND = "👤 Пользователь найден\n• {0}\n• ID: {1}\nВыдать доступ?"
    USER_TO_REVOKE_IS_FOUND = "👤 Пользователь найден\n• {0}\n• ID: {1}\nОтозвать доступ?"
    NO_ONE_WAIT_ACCESS = "Нет ожидающего подтверждения на выдачу доступа."
    USER_ADDED = "✅ Пользователь добавлен."
    USER_REVOKED = "✅ Доступ пользователя отозван."
    YOU_BEEN_ADDED = "✅ Администратор добавил вас в список пользователей."
    EMPTY_USER_LIST = "Список пользователей пуст."
    ADD_USER_CMD = "Использование: /add_user <telegram_id>"

    # validation errors
    USER_ID_NOT_INT = "Введите корректный Telegram ID, состоящий только из цифр."
    USER_ID_NOT_KNOWN = "❌ Пользователь ещё не взаимодействовал с ботом.\nПопросите пользователя открыть бота и нажать /start."
    NO_SUCH_USER = "❌ У пользователя нет доступа или он не найден в списке."


class BotInfo(CommonMessages, GmailMessages, InvoiceMessages, AuditLogMessages, MenuMessages, BankMessages):
    pass
