import logging

from integrations.gmail.auth import get_gmail_service
from integrations.gmail.search import find_bank_email

LOGGER = logging.getLogger(__name__)


def main() -> int:
    configure_logging()

    try:
        return run()
    except Exception as error:
        LOGGER.exception("Bank email workflow failed: %s", error)
        return 1


def run() -> int:
    LOGGER.info("Starting bank email search workflow")
    bank_email = find_bank_email(get_gmail_service())

    if bank_email is None:
        LOGGER.warning("No matching bank email found")
        print("No matching bank email found in the last 30 days.")
        return 0

    LOGGER.info("Found newest matching bank email: %s", bank_email.gmail_message_id)
    print(
        "\n".join(
            (
                "Newest matching bank email:",
                f"  Subject: {bank_email.subject}",
                f"  From: {bank_email.sender}",
                f"  Date: {bank_email.date}",
                f"  Gmail message id: {bank_email.gmail_message_id}",
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# def process_bank_email_workflow():
#     service = get_gmail_service()
#
#     messages = find_bank_emails(service)
#
#     if not messages:
#         logger.info("No bank emails found")
#         return
#
#     newest_message = messages[0]
#
#     email = get_message_metadata(service, newest_message)
#
#     if is_processed(email.message_id):
#         logger.info("Already processed")
#         return
#
#     logger.info("Processing email")
#
#     mark_as_processed(email.message_id)
