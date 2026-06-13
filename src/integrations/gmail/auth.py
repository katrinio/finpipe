"""Авторизация в Gmail API и создание клиентского сервиса."""

import json
import logging
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.infrastructure.security.token_cipher import TokenCipher
from src.storage.orm.user.gmail_account import GmailAccount
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)
GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
)


def get_gmail_service() -> Any:
    """Возвращает готовый Gmail API service с валидным OAuth-токеном."""

    account_credentials = load_connected_account_credentials()
    if account_credentials is not None:
        LOGGER.info("Loaded Gmail OAuth token from connected GmailAccount")
        return build("gmail", "v1", credentials=account_credentials, cache_discovery=False)

    # TODO(vps): удалить локальный token.json fallback после перевода всех Gmail API сценариев на GmailAccount.
    token_path = EnvVar.get_env_path("GMAIL_TOKEN_PATH")
    credentials = EnvVar.load_credentials(token_path, GMAIL_SCOPES)

    if credentials and credentials.valid and has_required_scopes(credentials):
        LOGGER.info("Loaded valid Gmail OAuth token")
    else:
        if credentials and credentials.valid and not has_required_scopes(credentials):
            LOGGER.warning(
                "Gmail OAuth token is missing required scopes; reauthorizing",
            )
        credentials = refresh_or_create_credentials(
            credentials,
            EnvVar.get_env_path("GMAIL_CREDENTIALS_PATH"),
        )
        save_credentials(credentials, token_path)

    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def load_connected_account_credentials() -> Credentials | None:
    """Создаёт OAuth credentials из refresh token подключённого GmailAccount."""

    owner_telegram_id = EnvVar.get_optional_env("BOT_OWNER_TELEGRAM_ID", "").strip()
    if not owner_telegram_id:
        return None

    gmail_account = GmailAccount.get_by_owner(int(owner_telegram_id))
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
    credentials.refresh(Request())
    return credentials


def load_oauth_client_credentials() -> tuple[str, str, str]:
    """Возвращает token_uri, client_id и client_secret для refresh flow."""

    env_client_id = EnvVar.get_optional_env("GMAIL_CLIENT_ID", "").strip()
    env_client_secret = EnvVar.get_optional_env("GMAIL_CLIENT_SECRET", "").strip()
    if env_client_id and env_client_secret:
        return "https://oauth2.googleapis.com/token", env_client_id, env_client_secret

    credentials_path = EnvVar.get_env_path("GMAIL_CREDENTIALS_PATH")
    client_config = json.loads(credentials_path.read_text(encoding="utf-8"))
    web_config = client_config.get("web") or client_config.get("installed")
    if not web_config:
        msg = "Gmail credentials file must contain web or installed client config"
        raise RuntimeError(msg)
    return web_config["token_uri"], web_config["client_id"], web_config["client_secret"]


def refresh_or_create_credentials(
    credentials: Credentials | None,
    credentials_path: Path,
) -> Credentials:
    """Обновляет истёкший токен или запускает первичную OAuth-авторизацию."""

    if credentials and credentials.expired and credentials.refresh_token:
        LOGGER.info("Refreshing expired Gmail OAuth token")
        credentials.refresh(Request())
        return credentials

    if not credentials_path.exists():
        message = f"Gmail credentials file not found: {credentials_path}"
        raise FileNotFoundError(message)

    LOGGER.info("Starting Gmail OAuth browser login")
    # TODO(vps): удалить desktop OAuth flow после полного перехода Gmail API на callback flow и постоянный домен.
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        GMAIL_SCOPES,
    )
    return flow.run_local_server(port=0)


def save_credentials(credentials: Credentials, token_path: Path) -> None:
    """Сохраняет OAuth-токен в файл для следующих запусков."""

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    LOGGER.info("Saved Gmail OAuth token")


def has_required_scopes(credentials: Credentials) -> bool:
    """Проверяет, выданы ли токену все необходимые Gmail scopes."""

    granted_scopes = set(credentials.scopes or [])
    required_scopes = set(GMAIL_SCOPES)
    return required_scopes.issubset(granted_scopes)
