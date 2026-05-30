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
from src.services.invoice.invoice_models import INVOICE_TEMPLATE_DETAILS
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


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

    data = invoice_period.as_template_data() | {"amount": amount}

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
        invoice_details=INVOICE_TEMPLATE_DETAILS,
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
