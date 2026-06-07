"""Workflow для генерации инвойса и отправки его в Telegram."""

from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.utils.credentials import EnvVar
from src.workflows.bricks.generate_invoice import generate_invoice_pdf


def generate_and_send_invoice() -> None:
    telegram_client = TelegramClient()

    pdf_path = generate_invoice_pdf()

    telegram_client.send_document(document_path=pdf_path)
    docx_path = pdf_path.with_suffix(".docx")
    telegram_client.send_document(document_path=docx_path)


def main() -> int:
    """Генерирует инвойс и отправляет связанные файлы в Telegram."""

    configure_logging()
    EnvVar.get_dotenv()
    generate_and_send_invoice()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
