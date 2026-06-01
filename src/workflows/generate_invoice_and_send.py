from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.utils.credentials import EnvVar
from src.workflows.generate_invoice import generate_invoice_pdf


def main() -> int:
    configure_logging()
    EnvVar.get_dotenv()

    pdf_path = generate_invoice_pdf()
    telegram_client = TelegramClient()

    telegram_client.send_document(
        document_path=pdf_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
