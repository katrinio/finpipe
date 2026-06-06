from src.constants import Message
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.services.transfer_request.transfer_request_generator import generate_transfer_request
from src.utils.credentials import EnvVar
from src.workflows.bricks.fetch_bank_email import fetch_bank_email_workflow
from src.workflows.bricks.generate_invoice import generate_invoice_pdf


def main() -> int:
    configure_logging()
    EnvVar.get_dotenv()

    fetch_bank_email_workflow()

    # fill_bank_pdf()
    transfer_request_pdf_path = generate_transfer_request()
    invoice_pdf_path = generate_invoice_pdf()

    telegram_client = TelegramClient()

    telegram_client.send_message(Message.BANK_RESPONSE)

    telegram_client.send_document(document_path=invoice_pdf_path)
    telegram_client.send_document(document_path=transfer_request_pdf_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
