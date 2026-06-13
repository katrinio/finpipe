"""OAuth flow подключения Gmail-аккаунта."""

import json
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from src.integrations.gmail.exceptions import (
    GmailOAuthError,
    GmailOAuthInvalidStateError,
    GmailOAuthStateExpiredError,
    GmailOAuthStateNotActiveError,
    GmailOAuthTokenExchangeError,
)
from src.storage.orm.system.oauth_session import OAuthSession
from src.utils.credentials import EnvVar

GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
)
LOGGER = logging.getLogger(__name__)


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
        LOGGER.info(
            "Gmail OAuth authorization URL built: redirect_uri=%s scopes=%s access_type=%s prompt=%s",
            callback_url,
            " ".join(GMAIL_SCOPES),
            "offline",
            "consent",
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
            raise GmailOAuthInvalidStateError("Invalid OAuth state")
        if oauth_session.status != "pending":
            raise GmailOAuthStateNotActiveError("OAuth state is not active")
        expires_at = oauth_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            OAuthSession.mark_expired(state)
            raise GmailOAuthStateExpiredError("OAuth state expired")
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
        try:
            flow = cls._build_flow(callback_url)
            flow.fetch_token(code=code)
            return flow.credentials
        except GmailOAuthError:
            raise
        except Exception as error:
            raise GmailOAuthTokenExchangeError("Failed to exchange OAuth code for Gmail credentials") from error

    @classmethod
    def _build_flow(cls, callback_url: str) -> Any:
        try:
            from google_auth_oauthlib.flow import Flow
        except ImportError as error:  # pragma: no cover
            raise GmailOAuthError("google-auth-oauthlib is not available") from error

        try:
            client_config, source, client_type, client_id = cls._load_client_config(callback_url)
            LOGGER.info(
                "Gmail OAuth flow initialized: source=%s client_type=%s client_id=%s redirect_uri=%s scopes=%s",
                source,
                client_type,
                client_id,
                callback_url,
                " ".join(GMAIL_SCOPES),
            )
            return Flow.from_client_config(client_config, list(GMAIL_SCOPES), redirect_uri=callback_url)
        except Exception as error:
            raise GmailOAuthError("Failed to initialize Gmail OAuth flow") from error

    @classmethod
    def _load_client_config(cls, callback_url: str) -> tuple[dict[str, Any], str, str, str]:
        env_client_id = EnvVar.get_optional_env("GMAIL_CLIENT_ID", "").strip()
        env_client_secret = EnvVar.get_optional_env("GMAIL_CLIENT_SECRET", "").strip()

        if env_client_id and env_client_secret:
            return (
                {
                    "web": {
                        "client_id": env_client_id,
                        "client_secret": env_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": [callback_url],
                    }
                },
                "env",
                "web",
                env_client_id,
            )

        credentials_path = EnvVar.get_env_path("GMAIL_CREDENTIALS_PATH")
        try:
            raw_config = json.loads(credentials_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise GmailOAuthError(f"Failed to read Gmail credentials file: {credentials_path}") from error
        except json.JSONDecodeError as error:
            raise GmailOAuthError(f"Failed to parse Gmail credentials file: {credentials_path}") from error

        if "web" in raw_config:
            client_type = "web"
        elif "installed" in raw_config:
            client_type = "installed"
        else:
            raise GmailOAuthError("Gmail credentials file must contain web or installed client config")

        client_config = raw_config[client_type]
        client_id = str(client_config.get("client_id") or "")
        redirect_uris = client_config.get("redirect_uris") or []
        if callback_url not in redirect_uris:
            LOGGER.warning(
                "Gmail OAuth callback URL is not listed in credentials redirect_uris: client_type=%s redirect_uri=%s",
                client_type,
                callback_url,
            )

        return raw_config, "credentials_file", client_type, client_id
