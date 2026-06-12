"""Основной workflow обработки письма банка и подготовки документов."""

from pathlib import Path

from src.constants import Message
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.services.bank.bank_extract import extract_amount
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from src.utils.credentials import EnvVar
from src.workflows.tasks.fetch_bank_email import fetch_bank_email_workflow
from src.workflows.tasks.generate_bank_confirmation import generate_bank_confirmation
from src.workflows.tasks.generate_conversion_order import generate_conversion_order_pdf
from src.workflows.tasks.generate_invoice import generate_invoice_pdf


def main() -> int:
    """Запускает bank flow: Gmail, Bank Confirmation, Conversion Order и Salary Invoice."""

    configure_logging()
    EnvVar.get_dotenv()
    build_storage_dependencies()
    telegram_client = TelegramClient()
    owner = AllowedUser.get_owner()
    if owner is None:
        raise RuntimeError("Owner is not bootstrapped in storage")
    telegram_client.send_message(owner.telegram_id, Message.START)

    bank_template_path = fetch_bank_email_workflow()
    if bank_template_path is None:
        # Без нового письма workflow ничего не генерирует и завершаетcя штатно.
        telegram_client.send_message(owner.telegram_id, Message.NO_NEW_BANK_EMAIL)
        return 0

    telegram_client.send_message(owner.telegram_id, Message.EMAIL_FETCHING_COMPLETED)

    bank_amount = extract_amount(bank_template_path)
    transfer_amount_text = f"{bank_amount:.2f}"

    bank_confirmation_path = generate_bank_confirmation(owner.telegram_id, bank_template_path, amount=bank_amount)
    telegram_client.send_message(owner.telegram_id, Message.BANK_CONFIRMATION_GENERATED)

    conversion_order_pdf_path = generate_conversion_order_pdf(owner.telegram_id, amount=transfer_amount_text)
    telegram_client.send_message(owner.telegram_id, Message.CONVERSION_ORDER_GENERATED)

    invoice_pdf_path = generate_invoice_pdf(telegram_id=owner.telegram_id)
    telegram_client.send_message(owner.telegram_id, Message.SALARY_INVOICE_GENERATED)

    try:
        send_bank_response(
            telegram_client,
            owner.telegram_id,
            invoice_pdf_path,
            conversion_order_pdf_path,
            bank_confirmation_path,
        )
    finally:
        _remove_generated_invoice_file(invoice_pdf_path)
        _remove_generated_invoice_file(invoice_pdf_path.with_suffix(".docx"))

    return 0


def send_bank_response(telegram_client: TelegramClient, chat_id: int, *document_paths: Path) -> None:
    """Отправляет итоговый ответ банку и все подготовленные документы."""

    telegram_client.send_message(chat_id, Message.BANK_RESPONSE)
    for document_path in document_paths:
        telegram_client.send_document(chat_id, document_path=document_path)


def _remove_generated_invoice_file(path: Path) -> None:
    """Удаляет временный сгенерированный файл Salary Invoice, если он существует."""

    if path.exists():
        path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
