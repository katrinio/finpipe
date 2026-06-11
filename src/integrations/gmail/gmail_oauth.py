"""OAuth flow подключения Gmail-аккаунта."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from src.integrations.gmail.exceptions import GmailOAuthError
from src.storage.orm.system.oauth_session import OAuthSession
from src.utils.credentials import EnvVar

GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
)


@dataclass(frozen=True, slots=True)
class GmailOAuthResult:
    """Данные, полученные после успешного OAuth-обмена с Gmail."""

    email: str | None
    refresh_token: str
    scopes: str | None
    expires_at: datetime | None


class GmailOAuth:
    """Инкапсулирует OAuth flow подключения Gmail."""

    @classmethod
    def build_authorization_url(
        cls,
        telegram_id: int,
        telegram_username: str | None,
        callback_url: str,
    ) -> tuple[str, OAuthSession]:
        """Создаёт URL авторизации и сохраняет временную OAuth-сессию."""

        state = cls._generate_state()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        session = OAuthSession.create(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            state=state,
            expires_at=expires_at,
        )
        flow = cls._build_flow(callback_url)
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state,
        )
        return authorization_url, session

    @classmethod
    def exchange_code(cls, code: str, callback_url: str) -> GmailOAuthResult:
        """Обменивает OAuth code на refresh token и метаданные аккаунта."""

        credentials = cls._exchange_code_for_credentials(code, callback_url)
        refresh_token = cls.extract_refresh_token(credentials)
        email = cls.extract_email(credentials)
        scopes_list = getattr(credentials, "scopes", None)
        scopes = " ".join(scopes_list) if scopes_list else None
        expires_at = getattr(credentials, "expiry", None)
        return GmailOAuthResult(email=email, refresh_token=refresh_token, scopes=scopes, expires_at=expires_at)

    @classmethod
    def validate_state(cls, state: str) -> OAuthSession:
        """Проверяет, что OAuth-сессия существует и ещё активна."""

        oauth_session = OAuthSession.get_by_state(state)
        if oauth_session is None:
            raise GmailOAuthError("Invalid OAuth state")
        if oauth_session.status != "pending":
            raise GmailOAuthError("OAuth state is not active")
        if oauth_session.expires_at < datetime.now(UTC):
            OAuthSession.mark_expired(state)
            raise GmailOAuthError("OAuth state expired")
        return oauth_session

    @classmethod
    def consume_state(cls, state: str) -> None:
        """Помечает OAuth state как использованный."""

        OAuthSession.mark_used(state)

    @classmethod
    def build_state_payload(
        cls,
        telegram_id: int,
        telegram_username: str | None,
    ) -> str:
        return f"{telegram_id}:{telegram_username or ''}:{cls._generate_state()}"

    @classmethod
    def parse_state_payload(cls, state: str) -> tuple[int, str | None]:
        telegram_id_text, username, _nonce = state.split(":", 2)
        return int(telegram_id_text), username or None

    @classmethod
    def extract_refresh_token(cls, credentials: object) -> str:
        refresh_token = getattr(credentials, "refresh_token", None)
        if not refresh_token:
            raise GmailOAuthError("Google OAuth did not return refresh_token")
        return refresh_token

    @classmethod
    def extract_email(cls, credentials: object) -> str | None:
        email = getattr(credentials, "email", None)
        if email:
            return email
        id_info = getattr(credentials, "id_token", None)
        if isinstance(id_info, dict):
            return id_info.get("email")
        return None

    @classmethod
    def _generate_state(cls) -> str:
        return secrets.token_urlsafe(32)

    @classmethod
    def _exchange_code_for_credentials(cls, code: str, callback_url: str) -> object:
        flow = cls._build_flow(callback_url)
        flow.fetch_token(code=code)
        return flow.credentials

    @classmethod
    def _build_flow(cls, callback_url: str) -> Any:
        try:
            from google_auth_oauthlib.flow import Flow
        except ImportError as error:  # pragma: no cover
            raise GmailOAuthError("google-auth-oauthlib is not available") from error

        credentials_path = EnvVar.get_env_path("GMAIL_CREDENTIALS_PATH")
        return Flow.from_client_secrets_file(str(credentials_path), list(GMAIL_SCOPES), redirect_uri=callback_url)
