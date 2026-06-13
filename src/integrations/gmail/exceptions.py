"""Исключения интеграции Gmail."""


class GmailSendError(RuntimeError):
    """Ошибка отправки письма через Gmail API."""


class GmailOAuthError(RuntimeError):
    """Ошибка Gmail OAuth flow."""


class GmailOAuthMissingCodeError(GmailOAuthError):
    """В callback отсутствует обязательный OAuth code."""


class GmailOAuthMissingStateError(GmailOAuthError):
    """В callback отсутствует обязательный OAuth state."""


class GmailOAuthProviderError(GmailOAuthError):
    """Google вернул ошибку вместо OAuth code."""


class GmailOAuthInvalidStateError(GmailOAuthError):
    """OAuth state не найден."""


class GmailOAuthStateNotActiveError(GmailOAuthError):
    """OAuth state уже использован или завершён."""


class GmailOAuthStateExpiredError(GmailOAuthError):
    """OAuth state истёк."""


class GmailOAuthTokenExchangeError(GmailOAuthError):
    """Не удалось обменять OAuth code на токены."""


__all__ = [
    "GmailOAuthError",
    "GmailOAuthInvalidStateError",
    "GmailOAuthMissingCodeError",
    "GmailOAuthMissingStateError",
    "GmailOAuthProviderError",
    "GmailOAuthStateExpiredError",
    "GmailOAuthStateNotActiveError",
    "GmailOAuthTokenExchangeError",
    "GmailSendError",
]
