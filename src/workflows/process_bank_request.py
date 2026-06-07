from src.constants import Message
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.services.bank.bank_extract import extract_amount
from src.utils.credentials import EnvVar
from src.workflows.bricks.fetch_bank_email import fetch_bank_email_workflow
from src.workflows.bricks.fill_bank_pdf import fill_bank_pdf_with_data
from src.workflows.bricks.generate_invoice import generate_invoice_pdf
from src.workflows.bricks.generate_transfer_request import generate_transfer_request_pdf


def main() -> int:
    configure_logging()
    EnvVar.get_dotenv()
    telegram_client = TelegramClient()
    telegram_client.send_message(Message.START)

    bank_template_path = fetch_bank_email_workflow()
    if bank_template_path is None:
        telegram_client.send_message(Message.NO_NEW_BANK_EMAIL)
        return 0

    telegram_client.send_message(Message.EMAIL_FETCHING_COMPLETED)

    bank_amount = extract_amount(bank_template_path)
    amount_text = f"{bank_amount:.2f}"

    bank_pdf_path = fill_bank_pdf_with_data(bank_template_path)
    telegram_client.send_message(Message.BANK_PDF_FILLED)

    transfer_request_pdf_path = generate_transfer_request_pdf(amount=amount_text)
    telegram_client.send_message(Message.TRANSACTION_REQUEST_GENERATED)

    invoice_pdf_path = generate_invoice_pdf(amount=amount_text)
    telegram_client.send_message(Message.INVOICE_GENERATED)

    telegram_client.send_message(Message.BANK_RESPONSE)

    telegram_client.send_document(document_path=invoice_pdf_path)
    telegram_client.send_document(document_path=transfer_request_pdf_path)
    telegram_client.send_document(document_path=bank_pdf_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
