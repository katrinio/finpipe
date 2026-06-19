"""Workflow для генерации Salary Invoice и отправки его в Telegram."""

import argparse
import logging
from datetime import date
from pathlib import Path

from src.constants import Dir, Format
from src.integrations.gmail.gmail_sender import send_email
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.services.invoice.context import build_invoice_period
from src.storage.orm.user.bank_details import BankDetails
from src.utils.credentials import EnvVar
from src.utils.files import delete_file
from src.workflows.tasks.generate_invoice import generate_invoice_pdf

LOGGER = logging.getLogger(__name__)

_MONTHS_RU = {
    1: "jan",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "aug",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dec",
}

_MONTHS_RU_GENITIVE = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


def _invoice_email_subject(account_holder: str, month: date | None = None) -> str:
    current = month or date.today()
    month_short = _MONTHS_RU[current.month]
    year_short = str(current.year)[2:]
    return f"Invoice {month_short}'{year_short} — {account_holder.title()}"


def _invoice_email_body(account_holder: str, account_holder_email: str, month: date | None = None) -> str:
    current = month or date.today()
    month_name = _MONTHS_RU_GENITIVE[current.month]
    return f"Добрый день.\nПрошу принять в работу инвойс за {month_name}.\n\nС уважением,\n{account_holder.title()}\n{account_holder_email}"


def _current_invoice_pdf_path() -> Path:
    invoice_number = build_invoice_period().invoice_number
    return Dir.INVOICE_OUTPUT_DIR / f"invoice-{invoice_number}.{Format.PDF}"


def send_invoice_email(telegram_id: int) -> None:
    """Отправляет уже сгенерированный Salary Invoice на email компании и удаляет файл."""

    bank_details = BankDetails.get_by_owner(telegram_id)
    account_holder = bank_details.account_holder if bank_details else ""
    account_holder_email = bank_details.account_holder_email if bank_details else ""

    # TODO: заменить на email компании из профиля или отдельного поля настроек
    to_email = EnvVar.get_required_env("EMAIL_DRY_RUN_RECIPIENT")
    pdf_path = _current_invoice_pdf_path()

    try:
        send_email(
            telegram_id=telegram_id,
            to_email=to_email,
            subject=_invoice_email_subject(account_holder),
            body=_invoice_email_body(account_holder, account_holder_email or ""),
            attachments=[pdf_path],
        )
        LOGGER.info("Invoice email sent for telegram_id=%s", telegram_id)
    finally:
        delete_file(pdf_path, LOGGER)


def discard_invoice_pdf() -> None:
    """Удаляет файл инвойса текущего месяца без отправки."""

    delete_file(_current_invoice_pdf_path(), LOGGER)


def generate_and_send_invoice(chat_id: int) -> None:
    """Генерирует Salary Invoice, отправляет в Telegram и оставляет PDF до подтверждения отправки."""

    telegram_client = TelegramClient()
    pdf_path = generate_invoice_pdf(telegram_id=chat_id)
    docx_path = pdf_path.with_suffix(".docx")

    # docx нужен только для генерации — удаляем сразу, PDF оставляем до решения пользователя
    delete_file(docx_path, LOGGER)
    telegram_client.send_document(chat_id, document_path=pdf_path)


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
