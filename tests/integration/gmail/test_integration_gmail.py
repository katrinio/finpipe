import json
import logging
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.infrastructure.security.token_cipher import TokenCipher
from src.integrations.gmail.oauth_token_bootstrap import GMAIL_SCOPES, normalize_client_config, save_credentials
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm.user.gmail_account import GmailAccount

load_dotenv()

LOGGER = logging.getLogger(__name__)


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
    if token_path.exists():
        LOGGER.info("Загружаю OAuth-токен Gmail из файла %s", token_path)
        creds = Credentials.from_authorized_user_file(str(token_path), list(GMAIL_SCOPES))
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            LOGGER.info("Обновляю истекший OAuth-токен Gmail")
            creds.refresh(Request())
            save_credentials(creds, token_path)
            return creds

    restored = restore_credentials_from_database(credentials_path, token_path)
    if restored is not None:
        return restored

    raise AssertionError("Gmail OAuth token is missing. Run scripts/generate_gmail_token.py")


def restore_credentials_from_database(credentials_path: Path, token_path: Path) -> Credentials | None:
    telegram_id = int(os.environ["BOT_OWNER_TELEGRAM_ID"])
    build_storage_dependencies()
    gmail_account = GmailAccount.get_by_owner(telegram_id)
    if gmail_account is None or not gmail_account.gmail_refresh_token:
        return None

    LOGGER.info("Восстанавливаю OAuth-токен Gmail из refresh token в базе")
    refresh_token = TokenCipher.decrypt(gmail_account.gmail_refresh_token)
    creds = build_credentials_from_refresh_token(credentials_path, refresh_token)
    creds.refresh(Request())
    save_credentials(creds, token_path)
    if not token_path.exists():
        raise AssertionError("Не удалось сохранить Gmail token.json")
    return creds


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

    client_config = normalize_client_config(json.loads(credentials_path.read_text(encoding="utf-8")))
    web_config = client_config["installed"]
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=web_config["token_uri"],
        client_id=web_config["client_id"],
        client_secret=web_config["client_secret"],
        scopes=list(GMAIL_SCOPES),
    )
