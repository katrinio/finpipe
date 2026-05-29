import logging

from src.integrations.gmail import get_gmail_service
from src.integrations.gmail.downloader import download_attachments
from src.integrations.gmail.search import find_bank_email
from src.logging_config import configure_logging
from src.storage import is_processed, mark_as_processed

LOGGER = logging.getLogger(__name__)


def main() -> int:
    configure_logging()

    try:
        process_bank_email_workflow()
    except Exception:
        LOGGER.exception("Bank email workflow failed")
        return 1

    return 0


def process_bank_email_workflow() -> None:
    LOGGER.info("Starting bank email workflow")
    service = get_gmail_service()
    bank_email = find_bank_email(service)

    if bank_email is None:
        LOGGER.info("No bank emails found")
        return

    if is_processed(bank_email.message_id):
        LOGGER.info("Bank email already processed: %s", bank_email.message_id)
        return

    LOGGER.info("Processing bank email: %s", bank_email.message_id)
    download_attachments(bank_email)
    mark_as_processed(bank_email.message_id)
    LOGGER.info("Marked bank email as processed: %s", bank_email.message_id)


if __name__ == "__main__":
    raise SystemExit(main())
