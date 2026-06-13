import json
import logging
import os
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.infrastructure.security.token_cipher import TokenCipher
from src.integrations.gmail.gmail_oauth import GMAIL_SCOPES, GmailOAuth
from src.integrations.gmail.settings import GmailOAuthSettings
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm.system.oauth_session import OAuthSession
from src.storage.orm.user.gmail_account import GmailAccount

load_dotenv()

LOGGER = logging.getLogger(__name__)
TOKEN_POLL_TIMEOUT_SECONDS = 180
TOKEN_POLL_INTERVAL_SECONDS = 2


@pytest.mark.skipif(
    os.getenv("RUN_GMAIL_E2E") != "true",
    reason="Gmail E2E requires manual Google OAuth callback; set RUN_GMAIL_E2E=true to run",
)
def test_gmail_integration() -> None:
    LOGGER.info("Проверяю настройки Gmail OAuth")

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH")
    token_path = os.getenv("GMAIL_TOKEN_PATH")

    assert credentials_path, "Не задана переменная окружения GMAIL_CREDENTIALS_PATH"
    assert token_path, "Не задана переменная окружения GMAIL_TOKEN_PATH"

    creds = load_or_create_credentials(Path(credentials_path), Path(token_path))

    assert creds is not None, "Не удалось получить OAuth-credentials для Gmail"
    assert creds.valid, "OAuth-credentials для Gmail невалидны"

    LOGGER.info("Создаю Gmail API client")
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    assert service is not None, "Не удалось создать Gmail API client"

    LOGGER.info("Запрашиваю последние 5 сообщений из Gmail")
    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=5,
        )
        .execute()
    )

    assert "messages" in results, "Ответ Gmail API не содержит ключ 'messages'"

    messages = results["messages"]

    assert isinstance(messages, list), "Поле 'messages' в ответе Gmail API не список"
    LOGGER.info("Получено сообщений из Gmail: %s", len(messages))

    for message in messages:
        assert "id" in message, "Сообщение Gmail не содержит ключ 'id'"

        LOGGER.info("Загружаю полные данные сообщения Gmail: %s", message["id"])
        full_message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
            )
            .execute()
        )

        assert "payload" in full_message, "Сообщение Gmail не содержит ключ 'payload'"
        assert "headers" in full_message["payload"], "Payload сообщения Gmail не содержит ключ 'headers'"

        headers = full_message["payload"]["headers"]

        subject = next(
            (header["value"] for header in headers if header["name"] == "Subject"),
            None,
        )

        assert subject is not None, "В headers сообщения Gmail нет темы Subject"
        assert isinstance(subject, str), "Тема Subject в сообщении Gmail не строка"
        LOGGER.info("Проверено сообщение Gmail с темой: %s", subject)

    LOGGER.info("Gmail integration test успешно завершен")


def load_or_create_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    creds: Credentials | None = None

    if token_path.exists():
        LOGGER.info("Загружаю OAuth-токен Gmail из файла %s", token_path)
        creds = Credentials.from_authorized_user_file(str(token_path), list(GMAIL_SCOPES))

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        LOGGER.info("Обновляю истекший OAuth-токен Gmail")
        creds.refresh(Request())
        save_credentials(creds, token_path)
        return creds

    return bootstrap_credentials_via_callback_flow(credentials_path, token_path)


def bootstrap_credentials_via_callback_flow(credentials_path: Path, token_path: Path) -> Credentials:
    LOGGER.info("Запускаю Gmail OAuth через существующий callback flow")

    callback_url = GmailOAuthSettings.get_callback_url()
    telegram_id = int(os.environ["BOT_OWNER_TELEGRAM_ID"])
    telegram_username = os.getenv("TELEGRAM_ADMIN_USERNAME")

    build_storage_dependencies()
    authorization_url, session = GmailOAuth.build_authorization_url(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        callback_url=callback_url,
    )

    LOGGER.info("Откройте URL для авторизации Gmail OAuth: %s", authorization_url)
    LOGGER.info("Ожидаю завершения callback для state=%s", session.state)

    gmail_account = wait_for_connected_gmail_account(telegram_id=telegram_id, state=session.state)
    assert gmail_account.gmail_refresh_token is not None, "В GmailAccount не сохранён refresh token"

    refresh_token = TokenCipher.decrypt(gmail_account.gmail_refresh_token)
    creds = build_credentials_from_refresh_token(credentials_path, refresh_token)
    creds.refresh(Request())
    save_credentials(creds, token_path)
    return creds


def wait_for_connected_gmail_account(telegram_id: int, state: str) -> GmailAccount:
    deadline = time.monotonic() + TOKEN_POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        session = OAuthSession.get_by_state(state)
        gmail_account = GmailAccount.get_by_owner(telegram_id)

        if session is not None and session.status == "used" and gmail_account is not None and gmail_account.gmail_refresh_token:
            return gmail_account

        if session is not None and session.status == "failed":
            raise AssertionError(f"OAuth callback завершился ошибкой: {session.error_message}")

        time.sleep(TOKEN_POLL_INTERVAL_SECONDS)

    raise AssertionError("Не дождались Gmail OAuth callback и сохранения refresh token")


def build_credentials_from_refresh_token(credentials_path: Path, refresh_token: str) -> Credentials:
    env_client_id = os.getenv("GMAIL_CLIENT_ID")
    env_client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    if env_client_id and env_client_secret:
        return Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env_client_id,
            client_secret=env_client_secret,
            scopes=list(GMAIL_SCOPES),
        )

    client_config = json.loads(credentials_path.read_text(encoding="utf-8"))
    web_config = client_config["web"]
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=web_config["token_uri"],
        client_id=web_config["client_id"],
        client_secret=web_config["client_secret"],
        scopes=list(GMAIL_SCOPES),
    )


def save_credentials(credentials: Credentials, token_path: Path) -> None:
    LOGGER.info("Сохраняю OAuth-токен Gmail в файл %s", token_path)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
