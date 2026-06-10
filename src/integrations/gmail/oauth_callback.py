"""Callback processing for Gmail OAuth."""

from __future__ import annotations

from dataclasses import dataclass

from src.integrations.gmail.account_service import GmailAccountService
from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.gmail.gmail_oauth import GmailOAuth, GmailOAuthResult
from src.storage.orm.system.oauth_session import OAuthSession


@dataclass(frozen=True, slots=True)
class OAuthCallbackResult:
    ok: bool
    message: str
    telegram_id: int | None
    redirect_url: str | None


class GmailOAuthCallbackService:
    @classmethod
    def handle_callback(
        cls,
        code: str | None,
        state: str | None,
        error: str | None,
        callback_url: str,
    ) -> OAuthCallbackResult:
        if error:
            return OAuthCallbackResult(False, f"OAuth error: {error}", None, None)
        if not code or not state:
            return OAuthCallbackResult(False, "Missing code or state", None, None)

        session = GmailOAuth.validate_state(state)
        result = GmailOAuth.exchange_code(code, callback_url)

        GmailAccountService.connect(
            telegram_id=session.telegram_id,
            email=result.email or "unknown",
            refresh_token=result.refresh_token,
        )
        OAuthSession.mark_used(state)

        return OAuthCallbackResult(True, "Gmail connected", session.telegram_id, None)

    @classmethod
    def validate_input(
        cls,
        code: str | None,
        state: str | None,
        error: str | None,
    ) -> None:
        if error:
            raise GmailOAuthError(error)
        if not code or not state:
            raise GmailOAuthError("Missing code or state")

    @classmethod
    def load_session(cls, state: str) -> OAuthSession:
        return GmailOAuth.validate_state(state)

    @classmethod
    def persist_connection(
        cls,
        session: OAuthSession,
        result: GmailOAuthResult,
    ) -> None:
        GmailAccountService.connect(
            telegram_id=session.telegram_id,
            email=result.email or "unknown",
            refresh_token=result.refresh_token,
        )

    @classmethod
    def mark_failed(
        cls,
        session: OAuthSession,
        error_message: str,
    ) -> None:
        OAuthSession.mark_failed(session.state, error_message)
