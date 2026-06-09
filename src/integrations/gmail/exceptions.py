"""Исключения интеграции Gmail."""


class GmailSendError(RuntimeError):
    """Ошибка отправки письма через Gmail API."""


class GmailOAuthError(RuntimeError):
    """Ошибка Gmail OAuth flow."""


__all__ = [
    "GmailOAuthError",
    "GmailSendError",
]
