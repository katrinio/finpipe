"""Workflow для генерации инвойса и отправки его в Telegram."""

import argparse

from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.utils.credentials import EnvVar
from src.workflows.tasks.generate_invoice import generate_invoice_pdf


def generate_and_send_invoice(chat_id: int) -> None:
    telegram_client = TelegramClient()

    pdf_path = generate_invoice_pdf()

    telegram_client.send_document(chat_id, document_path=pdf_path)
    docx_path = pdf_path.with_suffix(".docx")
    telegram_client.send_document(chat_id, document_path=docx_path)


def main() -> int:
    """Генерирует инвойс и отправляет связанные файлы в Telegram."""

    configure_logging()
    EnvVar.get_dotenv()
    parser = argparse.ArgumentParser(description="Generate and send invoice to a Telegram chat.")
    parser.add_argument("--chat-id", type=int, required=True, help="Telegram chat ID for delivery.")
    args = parser.parse_args()
    generate_and_send_invoice(args.chat_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
