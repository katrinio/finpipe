"""Шаг workflow для поиска письма банка и загрузки вложения."""

import logging
from pathlib import Path

from src.integrations.gmail import BankEmail, get_gmail_service
from src.integrations.gmail.downloader import download_attachments
from src.integrations.gmail.search import find_bank_email
from src.logging_config import configure_logging
from src.storage import is_processed, mark_as_processed

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """CLI-точка входа для загрузки нового bank PDF из Gmail."""

    configure_logging()

    try:
        attachment_path = fetch_bank_email_workflow()
        if attachment_path is not None:
            LOGGER.info("Attachment path: %s", attachment_path)
    except Exception:
        LOGGER.exception("Bank email workflow failed")
        return 1

    return 0


def fetch_bank_email_workflow(bank_email: BankEmail | None = None) -> Path | None:
    """
    Находит новое письмо банка, скачивает PDF
    и возвращает путь к вложению или `None`.
    """

    if bank_email is None:
        bank_email = find_bank_email(get_gmail_service())

    if bank_email is None:
        # Если новых писем банка нет, дальнейшая обработка не требуется.
        LOGGER.info("No bank emails found")
        return None

    if is_processed(bank_email.message_id):
        LOGGER.info("Bank email already processed: %s", bank_email.message_id)
        return None

    LOGGER.info("Processing bank email: %s", bank_email.message_id)
    attachment_path = download_attachments(bank_email)
    if attachment_path is None:
        # Без PDF-вложения письмо нельзя считать обработанным.
        LOGGER.warning("Skipping processed marker because no PDF attachment was downloaded")
        return None

    mark_as_processed(bank_email.message_id)
    LOGGER.info("Marked bank email as processed: %s", bank_email.message_id)
    return attachment_path


if __name__ == "__main__":
    raise SystemExit(main())
