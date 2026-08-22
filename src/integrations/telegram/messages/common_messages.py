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
(✍️ Подпись, 📄 Документы, 📝 Аудит и т.д.)
и не должны использоваться как индикаторы статуса.
"""


class MsgIcon:
    @staticmethod
    def success(text: str) -> str:
        return f"✅ {text}"

    @staticmethod
    def error(text: str) -> str:
        return f"❌ {text}"

    @staticmethod
    def warning(text: str) -> str:
        return f"⚠️ {text}"

    @staticmethod
    def waiting(text: str) -> str:
        return f"⏳ {text}"

    @staticmethod
    def status(is_ready: bool) -> str:
        return "✔️" if is_ready else "❗"


class CommonMessages:
    class General:
        HELP_HEADER = "📚 Доступные команды"
        WHOAMI_PREFIX = "👤 Информация о пользователе"

    class Errors:
        ACCESS_DENIED = "⛔ Доступ к Finpipe разрешён только владельцу бота."

        NO_SUCH_COMMAND = "🫥 Неизвестная команда."
        SYSTEM_ERROR = "💥 Произошла внутренняя ошибка."

    class Actions:
        USE_CONFIRMATION_BTN = "Используйте кнопки подтверждения ниже."
        OPERATION_CANCELLED = "Текущая операция отменена."
