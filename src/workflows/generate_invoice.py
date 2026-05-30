from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from src.constants import Format, Invoice
from src.logging_config import configure_logging
from src.services.invoice.invoice_context import build_invoice_period
from src.services.invoice.invoice_generator import generate_invoice
from src.services.invoice.invoice_models import InvoiceData
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)
DEFAULT_SERVICE_AGREEMENT_DATE = "01.05.2025"


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    amount = args.amount or EnvVar.get_required_env("INVOICE_AMOUNT")
    if not amount:
        parser.error("Pass --amount or set INVOICE_AMOUNT in .env")

    if not args.template.exists():
        LOGGER.error("Invoice template not found: %s", args.template)
        return 1

    invoice_period = build_invoice_period(args.invoice_date)
    output_pdf_path = args.output_dir / f"invoice-{invoice_period.invoice_number}.{Format.PDF}"

    data = InvoiceData(
        account_holder=EnvVar.get_required_env("ACCOUNT_HOLDER"),
        account_holder_address=EnvVar.get_required_env("ACCOUNT_HOLDER_ADDRESS"),
        account_bic=EnvVar.get_required_env("ACCOUNT_BIC"),
        account_iban=EnvVar.get_required_env("ACCOUNT_IBAN"),
        account_number=EnvVar.get_required_env("ACCOUNT_NUMBER"),
        amount=amount,
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

    LOGGER.info(
        "Generating invoice %s for period %s - %s",
        invoice_period.invoice_number,
        invoice_period.period_from,
        invoice_period.period_to,
    )
    generate_invoice(
        template_path=args.template,
        output_pdf_path=output_pdf_path,
        data=data,
    )

    LOGGER.info("Invoice saved to %s", output_pdf_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
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
        default=Invoice.TEMPLATE_PATH,
        help=f"Path to invoice DOCX template. Defaults to {Invoice.TEMPLATE_PATH}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Invoice.OUTPUT_DIR,
        help=f"Directory for generated files. Defaults to {Invoice.OUTPUT_DIR}.",
    )
    return parser


def parse_invoice_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        msg = "Expected date in YYYY-MM-DD format"
        raise argparse.ArgumentTypeError(msg) from error


if __name__ == "__main__":
    raise SystemExit(main())
