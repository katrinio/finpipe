"""Авторизация в Gmail API и создание клиентского сервиса."""

import logging
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.infrastructure.security.token_cipher import TokenCipher
from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.gmail.oauth_token_bootstrap import (
    GMAIL_SCOPES,
    load_credentials_config,
    normalize_client_config,
)
from src.storage.orm.user.gmail_account import GmailAccount
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def get_gmail_service() -> Any:
    """Возвращает готовый Gmail API service с валидным OAuth-токеном."""

    credentials = load_connected_account_credentials()
    if credentials is None:
        msg = "Gmail is not connected. Connect Gmail via the bot before using this workflow."
        raise GmailOAuthError(msg)

    LOGGER.info("Loaded Gmail OAuth token from connected GmailAccount")
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def load_connected_account_credentials() -> Credentials | None:
    """Создаёт OAuth credentials из refresh token подключённого GmailAccount."""

    owner_telegram_id = EnvVar.get_optional_env("BOT_OWNER_TELEGRAM_ID", "").strip()
    if not owner_telegram_id:
        return None

    telegram_id = int(owner_telegram_id)
    gmail_account = GmailAccount.get_by_owner(telegram_id)
    if gmail_account is None or not gmail_account.gmail_refresh_token:
        return None

    refresh_token = TokenCipher.decrypt(gmail_account.gmail_refresh_token)
    token_uri, client_id, client_secret = load_oauth_client_credentials()
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=list(GMAIL_SCOPES),
    )

    try:
        credentials.refresh(Request())
    except RefreshError as exc:
        LOGGER.warning("Gmail token refresh failed for Telegram user %s: %s", telegram_id, exc)
        GmailAccount.set_gmail_connection_error(telegram_id, str(exc))
        return None

    GmailAccount.set_gmail_connection_error(telegram_id, "")
    return credentials


def load_oauth_client_credentials() -> tuple[str, str, str]:
    """Возвращает token_uri, client_id и client_secret для refresh flow."""

    env_client_id = EnvVar.get_optional_env("GMAIL_CLIENT_ID", "").strip()
    env_client_secret = EnvVar.get_optional_env("GMAIL_CLIENT_SECRET", "").strip()
    if env_client_id and env_client_secret:
        return "https://oauth2.googleapis.com/token", env_client_id, env_client_secret

    credentials_path = EnvVar.get_env_path("GMAIL_CREDENTIALS_PATH")
    client_config = load_credentials_config(credentials_path)
    normalized = normalize_client_config(client_config)
    oauth_config = normalized["installed"]
    return oauth_config["token_uri"], oauth_config["client_id"], oauth_config["client_secret"]
