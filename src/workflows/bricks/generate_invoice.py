"""Шаг workflow для генерации инвойса."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from src.constants import Dir, Format
from src.logging_config import configure_logging
from src.services.invoice.invoice_context import build_invoice_period
from src.services.invoice.invoice_generator import generate_invoice
from src.services.invoice.invoice_models import InvoiceData
from src.storage.dependencies import build_storage_dependencies
from src.storage.repositories.repositories import InvoiceHistoryRepository
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)
DEFAULT_SERVICE_AGREEMENT_DATE = "01.05.2025"


def generate_invoice_pdf(
    amount: str | None = None,
    invoice_date: date | None = None,
    template_path: Path = Dir.INVOICE_TEMPLATE,
    output_dir: Path = Dir.INVOICE_OUTPUT_DIR,
    invoice_history_repository: InvoiceHistoryRepository | None = None,
) -> Path:
    """
    Генерирует PDF-инвойс на указанную сумму
    и возвращает путь к файлу.
    """

    invoice_period = build_invoice_period(invoice_date)
    output_pdf_path = output_dir / f"invoice-{invoice_period.invoice_number}.{Format.PDF}"

    invoice_data = InvoiceData(
        account_holder=EnvVar.get_required_env("ACCOUNT_HOLDER"),
        account_holder_address=EnvVar.get_required_env("ACCOUNT_HOLDER_ADDRESS"),
        account_bic=EnvVar.get_required_env("ACCOUNT_BIC"),
        account_iban=EnvVar.get_required_env("ACCOUNT_IBAN"),
        account_number=EnvVar.get_required_env("ACCOUNT_NUMBER"),
        amount=amount or EnvVar.get_required_env("INVOICE_AMOUNT"),
        bank_name=EnvVar.get_required_env("BANK_NAME"),
        company_address=EnvVar.get_required_env("COMPANY_ADDRESS"),
        company_name=EnvVar.get_required_env("COMPANY_NAME"),
        date_from=invoice_period.period_from,
        date_to=invoice_period.period_to,
        invoice_date=invoice_period.invoice_date,
        invoice_number=invoice_period.invoice_number,
        service_agreement_date=EnvVar.get_optional_env(
            "SERVICE_AGREEMENT_DATE",
            DEFAULT_SERVICE_AGREEMENT_DATE,
        ),
    )

    repository = invoice_history_repository or build_storage_dependencies().invoice_history
    invoice_number = invoice_period.invoice_number

    if repository.invoice_exists(invoice_number):
        LOGGER.warning("Invoice %s already exists", invoice_number)
        msg = f"Invoice {invoice_number} already exists."
        raise ValueError(msg)

    generate_invoice(
        template_path=template_path,
        output_pdf_path=output_pdf_path,
        data=invoice_data,
    )

    repository.add_invoice(invoice_number)

    return output_pdf_path


def main(argv: Sequence[str] | None = None) -> int:
    """CLI-точка входа для генерации инвойса."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    amount = args.amount or EnvVar.get_required_env("INVOICE_AMOUNT")

    if not args.template.exists():
        LOGGER.error("Invoice template not found: %s", args.template)
        return 1

    storage = build_storage_dependencies()
    invoice_period = build_invoice_period(args.invoice_date)

    LOGGER.info(
        "Generating invoice %s for period %s - %s",
        invoice_period.invoice_number,
        invoice_period.period_from,
        invoice_period.period_to,
    )
    pdf_path = generate_invoice_pdf(
        amount=amount,
        invoice_date=args.invoice_date,
        template_path=args.template,
        output_dir=args.output_dir,
        invoice_history_repository=storage.invoice_history,
    )

    LOGGER.info("Invoice saved to %s", pdf_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Создаёт CLI-парсер для генерации инвойса."""

    parser = argparse.ArgumentParser(
        description="Generate salary invoice PDF and DOCX files.",
    )
    parser.add_argument(
        "--amount",
        help="Invoice amount in EUR. Defaults to INVOICE_AMOUNT from .env.",
    )
    parser.add_argument(
        "--date",
        dest="invoice_date",
        type=parse_invoice_date,
        default=None,
        help="Invoice date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Dir.INVOICE_TEMPLATE,
        help=f"Path to invoice DOCX template. Defaults to {Dir.INVOICE_TEMPLATE}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Dir.INVOICE_OUTPUT_DIR,
        help=f"Directory for generated files. Defaults to {Dir.INVOICE_OUTPUT_DIR}.",
    )
    return parser


def parse_invoice_date(value: str) -> date:
    """Преобразует строку CLI в дату инвойса."""

    try:
        return date.fromisoformat(value)
    except ValueError as error:
        msg = "Expected date in YYYY-MM-DD format"
        raise argparse.ArgumentTypeError(msg) from error


if __name__ == "__main__":
    raise SystemExit(main())
