"""Загрузка PDF-вложений из письма банка."""

import base64
import logging
from pathlib import Path
from typing import Any

from src.constants import Dir
from src.integrations.gmail.gmail_models import BankEmail
from src.utils.utils import Utils

LOGGER = logging.getLogger(__name__)


def download_attachments(bank_email: BankEmail, service: Any) -> Path | None:
    """
    Скачивает первое PDF-вложение из письма банка
    и возвращает путь к сохранённому файлу.
    """

    LOGGER.info("Downloading PDF attachments from Gmail message: %s", bank_email.message_id)

    user_id = "me"
    attachment_stem = f"bank-form-{Utils.today()}"

    Dir.ATTACHMENTS.mkdir(parents=True, exist_ok=True)

    gmail_message = service.users().messages().get(userId=user_id, id=bank_email.message_id).execute()

    payload = gmail_message.get("payload", {})
    parts = payload.get("parts", [])
    saved_path: Path | None = None

    for part in parts:
        if part.get("filename") and part["body"].get("attachmentId"):
            filename = part["filename"]

            if filename.endswith(".pdf"):
                # Для bank flow достаточно первого PDF-вложения из письма.
                attachment_id = part["body"]["attachmentId"]
                LOGGER.info("Downloading Gmail PDF attachment")
                attachment_payload = (
                    service.users()
                    .messages()
                    .attachments()
                    .get(
                        userId=user_id,
                        id=attachment_id,
                        messageId=bank_email.message_id,
                    )
                    .execute()
                )

                file_data = base64.urlsafe_b64decode(attachment_payload["data"].encode("UTF-8"))

                attachment_path = Dir.ATTACHMENTS / f"{attachment_stem}.pdf"
                with attachment_path.open("wb") as file_handle:
                    file_handle.write(file_data)

                saved_path = attachment_path
                LOGGER.info("Saved Gmail PDF attachment")
                break

    if saved_path is None:
        LOGGER.warning("No PDF attachments found in Gmail message: %s", bank_email.message_id)
        return None

    return saved_path
