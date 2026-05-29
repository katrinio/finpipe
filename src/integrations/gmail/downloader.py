import base64
import logging
import os

from src.integrations.gmail import BankEmail, get_gmail_service
from utils import Utils

LOGGER = logging.getLogger(__name__)


def download_attachments(bank_email: BankEmail) -> None:
    LOGGER.info("Start downloading attachment process from: %s", bank_email.message_id)

    service = get_gmail_service()
    user_id = "me"
    new_filename = f"Obavestenje o prilivu {Utils.today()}"

    os.makedirs("attachments", exist_ok=True)

    message = service.users().messages().get(userId=user_id, id=bank_email.message_id).execute()

    payload = message.get("payload", {})
    parts = payload.get("parts", [])

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

                LOGGER.info("Saving attach: %s", filename)

                filepath = os.path.join("attachments", new_filename)
                with open(filepath, "wb") as f:
                    f.write(file_data)

                LOGGER.info("Attach saved: %s", new_filename)
