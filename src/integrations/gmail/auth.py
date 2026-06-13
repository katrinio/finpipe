"""Авторизация в Gmail API и создание клиентского сервиса."""

import logging
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)
GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
)


def get_gmail_service() -> Any:
    """Возвращает готовый Gmail API service с валидным OAuth-токеном."""

    # TODO(vps): заменить локальный token.json на создание Gmail service из refresh token в GmailAccount.
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
