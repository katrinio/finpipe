import logging
import os

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

LOGGER = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def test_gmail_integration() -> None:
    LOGGER.info("Проверяю настройки Gmail OAuth")

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH")
    token_path = os.getenv("GMAIL_TOKEN_PATH")

    assert credentials_path, "Не задана переменная окружения GMAIL_CREDENTIALS_PATH"
    assert token_path, "Не задана переменная окружения GMAIL_TOKEN_PATH"

    creds: Credentials | None = None

    if os.path.exists(token_path):
        LOGGER.info("Загружаю OAuth-токен Gmail из файла %s", token_path)
        creds = Credentials.from_authorized_user_file(
            token_path,
            SCOPES,
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            LOGGER.info("Обновляю истекший OAuth-токен Gmail")
            creds.refresh(Request())

        else:
            LOGGER.info("Запускаю браузерную авторизацию Gmail OAuth")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        LOGGER.info("Сохраняю OAuth-токен Gmail в файл %s", token_path)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    assert creds is not None, "Не удалось получить OAuth-credentials для Gmail"
    assert creds.valid, "OAuth-credentials для Gmail невалидны"

    LOGGER.info("Создаю Gmail API client")
    service = build("gmail", "v1", credentials=creds)

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
