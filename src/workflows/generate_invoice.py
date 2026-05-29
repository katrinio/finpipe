from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from constants import Format, Invoice
from src.services.invoice.context import build_invoice_period
from src.services.invoice.generator import generate_invoice

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class InvoiceTemplateDetails:
    placeholder_aliases: dict[str, tuple[str, ...]]


INVOICE_TEMPLATE_DETAILS = InvoiceTemplateDetails(
    placeholder_aliases={
        "invoice_number": ("invoiceId",),
        "date": ("invoiceDate",),
        "period_from": ("dateFrom",),
        "period_to": ("dateTo",),
        "amount": ("amount",),
    },
)


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    amount = args.amount or os.getenv("INVOICE_AMOUNT")
    if not amount:
        parser.error("Pass --amount or set INVOICE_AMOUNT in .env")

    if not args.template.exists():
        LOGGER.error("Invoice template not found: %s", args.template)
        return 1

    invoice_period = build_invoice_period(args.invoice_date)
    output_pdf_path = args.output_dir / f"invoice-{invoice_period.invoice_number}.{Format.PDF}"

    data = invoice_period.as_template_data() | {"amount": amount}

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
