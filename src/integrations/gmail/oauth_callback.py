"""Обработка callback-запроса Gmail OAuth."""

import logging
from dataclasses import dataclass

from src.integrations.gmail.account_service import GmailAccountService
from src.integrations.gmail.exceptions import (
    GmailOAuthError,
    GmailOAuthInvalidStateError,
    GmailOAuthMissingCodeError,
    GmailOAuthMissingStateError,
    GmailOAuthProviderError,
    GmailOAuthStateExpiredError,
    GmailOAuthStateNotActiveError,
    GmailOAuthTokenExchangeError,
)
from src.integrations.gmail.gmail_oauth import GmailOAuth, GmailOAuthResult
from src.integrations.gmail.settings import GmailOAuthSettings
from src.storage.orm.system.oauth_session import OAuthSession

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OAuthCallbackResult:
    """Результат обработки Gmail OAuth callback."""

    ok: bool
    message: str
    telegram_id: int | None
    redirect_url: str | None


class GmailOAuthCallbackService:
    """Связывает callback Gmail OAuth с локальным хранилищем."""

    @classmethod
    def handle_callback(
        cls,
        code: str | None,
        state: str | None,
        error: str | None,
    ) -> OAuthCallbackResult:
        """Обрабатывает callback целиком и сохраняет Gmail-подключение."""

        callback_url = GmailOAuthSettings.get_callback_url()
        cls.validate_input(code=code, state=state, error=error)
        assert state is not None
        assert code is not None

        session: OAuthSession | None = None
        try:
            session = cls.load_session(state)
            LOGGER.info("OAuth session validated for telegram_id=%s", session.telegram_id)
            result = GmailOAuth.exchange_code(code, callback_url)
            cls.persist_connection(session, result)
            GmailOAuth.consume_state(state)
            LOGGER.info("OAuth flow completed for telegram_id=%s", session.telegram_id)
            return OAuthCallbackResult(True, "Gmail connected", session.telegram_id, None)
        except (
            GmailOAuthMissingCodeError,
            GmailOAuthMissingStateError,
            GmailOAuthInvalidStateError,
            GmailOAuthStateNotActiveError,
            GmailOAuthStateExpiredError,
            GmailOAuthProviderError,
            GmailOAuthTokenExchangeError,
        ) as exc:
            cls._log_callback_error(exc, session)
            if session is not None:
                cls.mark_failed(session, str(exc))
            raise
        except GmailOAuthError as exc:
            LOGGER.error("Callback processing failed for telegram_id=%s: %s", session.telegram_id if session is not None else None, exc)
            if session is not None:
                cls.mark_failed(session, str(exc))
            raise
        except Exception as exc:
            LOGGER.error("Callback processing failed for telegram_id=%s: %s", session.telegram_id if session is not None else None, exc)
            if session is not None:
                cls.mark_failed(session, f"Callback processing failed: {exc}")
            raise GmailOAuthError(f"Callback processing failed: {exc}") from exc

    @classmethod
    def validate_input(
        cls,
        code: str | None,
        state: str | None,
        error: str | None,
    ) -> None:
        """Проверяет обязательные параметры callback-запроса."""

        if error:
            raise GmailOAuthProviderError(f"OAuth error: {error}")
        if not state:
            LOGGER.warning("Missing code/state")
            raise GmailOAuthMissingStateError("Missing state")
        if not code:
            LOGGER.warning("Missing code/state")
            raise GmailOAuthMissingCodeError("Missing code")

    @classmethod
    def load_session(cls, state: str) -> OAuthSession:
        """Загружает и валидирует OAuth-сессию по state."""

        return GmailOAuth.validate_state(state)

    @classmethod
    def persist_connection(
        cls,
        session: OAuthSession,
        result: GmailOAuthResult,
    ) -> None:
        """Сохраняет успешное Gmail-подключение пользователя."""

        GmailAccountService.connect(
            telegram_id=session.telegram_id,
            email=result.email or "unknown",
            refresh_token=result.refresh_token,
        )
        LOGGER.info("Gmail account connected for telegram_id=%s", session.telegram_id)

    @classmethod
    def mark_failed(
        cls,
        session: OAuthSession,
        error_message: str,
    ) -> None:
        """Помечает OAuth-сессию завершившейся ошибкой."""

        OAuthSession.mark_failed(session.state, error_message)

    @staticmethod
    def _log_callback_error(error: GmailOAuthError, session: OAuthSession | None) -> None:
        telegram_id = session.telegram_id if session is not None else None
        if isinstance(error, (GmailOAuthMissingCodeError, GmailOAuthMissingStateError)):
            LOGGER.warning("Missing code/state for telegram_id=%s", telegram_id)
            return
        if isinstance(error, GmailOAuthInvalidStateError):
            LOGGER.warning("Invalid state for telegram_id=%s", telegram_id)
            return
        if isinstance(error, GmailOAuthStateNotActiveError):
            LOGGER.warning("Reused state for telegram_id=%s", telegram_id)
            return
        if isinstance(error, GmailOAuthStateExpiredError):
            LOGGER.warning("Expired state for telegram_id=%s", telegram_id)
            return
        if isinstance(error, GmailOAuthTokenExchangeError):
            LOGGER.error("Token exchange failed for telegram_id=%s", telegram_id)
            return
        if isinstance(error, GmailOAuthProviderError):
            LOGGER.error("Callback processing failed for telegram_id=%s: %s", telegram_id, error)
            return
        LOGGER.error("Callback processing failed for telegram_id=%s: %s", telegram_id, error)
