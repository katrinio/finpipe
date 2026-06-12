"""Исключения интеграции Telegram Bot API."""


class TelegramApiError(RuntimeError):
    """Telegram API вернул неуспешный ответ."""
