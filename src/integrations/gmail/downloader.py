import base64
import logging
from pathlib import Path

from src.constants import Dir
from src.integrations.gmail import BankEmail, get_gmail_service
from src.utils import Utils

LOGGER = logging.getLogger(__name__)


def download_attachments(bank_email: BankEmail) -> Path | None:
    LOGGER.info("Downloading PDF attachments from Gmail message: %s", bank_email.message_id)

    service = get_gmail_service()
    user_id = "me"
    new_filename = f"bank-form-{Utils.today()}"

    Dir.ATTACHMENTS.mkdir(parents=True, exist_ok=True)

    message = service.users().messages().get(userId=user_id, id=bank_email.message_id).execute()

    payload = message.get("payload", {})
    parts = payload.get("parts", [])
    saved_path: Path | None = None

    for part in parts:
        if part.get("filename") and part["body"].get("attachmentId"):
            filename = part["filename"]

            if filename.endswith(".pdf"):
                attachment_id = part["body"]["attachmentId"]
                LOGGER.info("Downloading file: %s", filename)
                attachment = (
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

                file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))

                LOGGER.info("Saving Gmail PDF attachment: %s", filename)

                filepath = Dir.ATTACHMENTS / f"{new_filename}.pdf"
                with filepath.open("wb") as file_handle:
                    file_handle.write(file_data)

                saved_path = filepath
                LOGGER.info("Saved Gmail PDF attachment to %s", filepath)
                break

    if saved_path is None:
        LOGGER.warning("No PDF attachments found in Gmail message: %s", bank_email.message_id)
        return None

    return saved_path
