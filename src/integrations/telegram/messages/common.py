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


class CommonMessagesV2:
    class General:
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

    class Status:
        PROJECT_RUNNING = "🟢 Finpipe работает."
        TELEGRAM_API_OK = Msg.success("Telegram API работает.")

    class Errors:
        ACCESS_DENIED = "⛔ У вас пока нет доступа к Finpipe.\nНажмите «Кто я» и отправьте свой Telegram ID владельцу бота."

        NO_SUCH_COMMAND = "🫥 Неизвестная команда."
        SYSTEM_ERROR = "💥 Произошла внутренняя ошибка."

    class Actions:
        USE_CONFIRMATION_BTN = "Используйте кнопки подтверждения ниже."


class CommonMessages(CommonMessagesV2):
    pass
