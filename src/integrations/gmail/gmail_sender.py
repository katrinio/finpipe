"""Отправка новых писем через Gmail API."""

import base64
import logging
from pathlib import Path
from typing import Any

from src.integrations.gmail.auth import get_gmail_service
from src.integrations.gmail.exceptions import GmailSendError
from src.services.email import EmailBuilder
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)
DRY_RUN_DEFAULT = "false"
DRY_RUN_FAKE_MESSAGE_ID = "dry-run-message-id"
SEND_FAILURE_MESSAGE = "Failed to send email via Gmail API"
MISSING_MESSAGE_ID_MESSAGE = "Gmail API did not return a message id"


class GmailSender:
    """Отправляет MIME-письма через Gmail API и скрывает детали клиента."""

    def __init__(
        self,
        telegram_id: int,
        email_builder: EmailBuilder | None = None,
        service: Any | None = None,
    ) -> None:
        self._telegram_id = telegram_id
        self._email_builder = email_builder or EmailBuilder()
        self._service = service

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
        cc: str = "",
    ) -> str:
        """Отправляет новое письмо и возвращает Gmail message id."""

        resolved_to_email = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", to_email)
        dry_run = EnvVar.get_optional_env("EMAIL_DRY_RUN", DRY_RUN_DEFAULT).lower() == "true"
        attachment_list = list(attachments or [])

        LOGGER.info("Sending Gmail message")
        LOGGER.info("Attachments count: %s", len(attachment_list))
        if cc:
            LOGGER.info("CC: %s", cc)

        if dry_run:
            LOGGER.info("EMAIL_DRY_RUN=true, email will not be sent")
            LOGGER.info("Returned Gmail message id: %s", DRY_RUN_FAKE_MESSAGE_ID)
            return DRY_RUN_FAKE_MESSAGE_ID

        raw_message = self._email_builder.build_email(
            to_email=resolved_to_email,
            subject=subject,
            body=body,
            attachments=attachment_list,
            cc=cc,
        )
        encoded_message = base64.urlsafe_b64encode(raw_message).decode("utf-8")

        try:
            response = (
                self._service_or_default()
                .users()
                .messages()
                .send(
                    userId="me",
                    body={"raw": encoded_message},
                )
                .execute()
            )
        except Exception as error:
            raise GmailSendError(SEND_FAILURE_MESSAGE) from error

        message_id = self._extract_message_id(response)
        LOGGER.info("Gmail message sent successfully")
        LOGGER.info("Returned Gmail message id: %s", message_id)
        return message_id

    def send_reply(
        self,
        thread_id: str,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
        cc: str = "",
    ) -> str:
        """Отправляет ответ в существующий тред и возвращает Gmail message id."""

        resolved_to_email = EnvVar.get_optional_env("EMAIL_DRY_RUN_RECIPIENT", to_email)
        dry_run = EnvVar.get_optional_env("EMAIL_DRY_RUN", DRY_RUN_DEFAULT).lower() == "true"
        attachment_list = list(attachments or [])

        LOGGER.info("Sending Gmail reply to thread %s", thread_id)
        LOGGER.info("Attachments count: %s", len(attachment_list))
        if cc:
            LOGGER.info("CC: %s", cc)

        if dry_run:
            LOGGER.info("EMAIL_DRY_RUN=true, reply will not be sent")
            LOGGER.info("Returned Gmail message id: %s", DRY_RUN_FAKE_MESSAGE_ID)
            return DRY_RUN_FAKE_MESSAGE_ID

        raw_message = self._email_builder.build_email(
            to_email=resolved_to_email,
            subject=subject,
            body=body,
            attachments=attachment_list,
            cc=cc,
        )
        encoded_message = base64.urlsafe_b64encode(raw_message).decode("utf-8")

        try:
            response = (
                self._service_or_default()
                .users()
                .messages()
                .send(
                    userId="me",
                    body={"raw": encoded_message, "threadId": thread_id},
                )
                .execute()
            )
        except Exception as error:
            raise GmailSendError(SEND_FAILURE_MESSAGE) from error

        message_id = self._extract_message_id(response)
        LOGGER.info("Gmail reply sent successfully")
        LOGGER.info("Returned Gmail message id: %s", message_id)
        return message_id

    def _service_or_default(self) -> Any:
        """Возвращает заранее переданный сервис или создаёт Gmail client."""

        return self._service or get_gmail_service(self._telegram_id)

    def _extract_message_id(self, response: dict[str, Any]) -> str:
        """Извлекает Gmail message id из ответа API."""

        message_id = response.get("id")
        if not isinstance(message_id, str) or not message_id:
            raise GmailSendError(MISSING_MESSAGE_ID_MESSAGE)

        return message_id


def send_email(
    telegram_id: int,
    to_email: str,
    subject: str,
    body: str,
    attachments: list[Path] | None = None,
    cc: str = "",
) -> str:
    """Отправляет новое письмо через стандартный GmailSender."""

    return GmailSender(telegram_id=telegram_id).send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        attachments=attachments,
        cc=cc,
    )


def send_reply(
    telegram_id: int,
    thread_id: str,
    to_email: str,
    subject: str,
    body: str,
    attachments: list[Path] | None = None,
    cc: str = "",
) -> str:
    """Отправляет ответ в существующий тред через стандартный GmailSender."""

    return GmailSender(telegram_id=telegram_id).send_reply(
        thread_id=thread_id,
        to_email=to_email,
        subject=subject,
        body=body,
        attachments=attachments,
        cc=cc,
    )
