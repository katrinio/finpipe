"""Workflow для генерации Salary Invoice и отправки его в Telegram."""

import argparse
import logging

from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.utils.credentials import EnvVar
from src.utils.files import delete_file
from src.workflows.tasks.generate_invoice import generate_invoice_pdf

LOGGER = logging.getLogger(__name__)


def generate_and_send_invoice(chat_id: int) -> None:
    """Генерирует Salary Invoice, отправляет его в Telegram и удаляет временные файлы."""

    telegram_client = TelegramClient()
    pdf_path = generate_invoice_pdf(telegram_id=chat_id)
    docx_path = pdf_path.with_suffix(".docx")

    try:
        telegram_client.send_document(chat_id, document_path=pdf_path)
    finally:
        delete_file(docx_path, LOGGER)
        delete_file(pdf_path, LOGGER)


def main() -> int:
    """Генерирует Salary Invoice и отправляет связанные файлы в Telegram."""

    configure_logging()
    EnvVar.get_dotenv()
    parser = argparse.ArgumentParser(description="Generate and send invoice to a Telegram chat.")
    parser.add_argument("--chat-id", type=int, required=True, help="Telegram chat ID for delivery.")
    args = parser.parse_args()
    generate_and_send_invoice(args.chat_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
