"""Исключения интеграции Gmail."""


class GmailSendError(RuntimeError):
    """Ошибка отправки письма через Gmail API."""
