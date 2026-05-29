import logging
import os
from typing import Any

from dotenv import load_dotenv

from .auth import ENV_PATH
from .gmail_models import BankEmail

LOGGER = logging.getLogger(__name__)
USER_ID = "me"
LOOKBACK_WINDOW = "30d"
METADATA_HEADERS = ("Subject", "From", "Date")


def find_bank_email(service: Any) -> BankEmail | None:
    LOGGER.info("Searching Gmail for bank email from the last %s", LOOKBACK_WINDOW)

    response = service.users().messages().list(userId=USER_ID, q=build_bank_email_query(), maxResults=10).execute()
    messages = response.get("messages", [])
    if not messages:
        LOGGER.info("No Gmail messages matched the configured bank email subject")
        return None

    newest_message = max(
        (fetch_message_metadata(service, message["id"]) for message in messages),
        key=lambda message: int(message.get("internalDate", "0")),
    )

    return build_bank_email_result(newest_message)


def build_bank_email_query() -> str:
    load_dotenv(ENV_PATH)
    subject = os.getenv("BANK_EMAIL_SUBJECT")
    from_user = os.getenv("BANK_EMAIL_FROM")

    if not subject:
        message = "Missing required environment variable: BANK_EMAIL_SUBJECT"
        raise RuntimeError(message)

    if not from_user:
        message = "Missing required environment variable: BANK_EMAIL_FROM"
        raise RuntimeError(message)

    subject = subject.replace('"', r"\"")
    from_user = from_user.replace('"', r"\"")
    return f'subject:"{subject}" from:"{from_user}" newer_than:{LOOKBACK_WINDOW} has:attachment'


def fetch_message_metadata(service: Any, message_id: str) -> dict[str, Any]:
    return (
        service.users()
        .messages()
        .get(
            userId=USER_ID,
            id=message_id,
            format="metadata",
            metadataHeaders=list(METADATA_HEADERS),
        )
        .execute()
    )


def build_bank_email_result(message: dict[str, Any]) -> BankEmail:
    headers = extract_headers(message)
    return BankEmail(
        subject=headers.get("subject", ""),
        sender=headers.get("from", ""),
        date=headers.get("date", ""),
        message_id=message["id"],
        thread_id=message["threadId"],
    )


def extract_headers(message: dict[str, Any]) -> dict[str, str]:
    return {header.get("name", "").lower(): header.get("value", "") for header in message.get("payload", {}).get("headers", []) if header.get("name")}
