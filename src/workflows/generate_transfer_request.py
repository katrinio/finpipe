from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from src.constants import Format, TransferRequest
from src.logging_config import configure_logging
from src.services.invoice.invoice_context import build_invoice_period
from src.services.transfer_request.transfer_request_generator import generate_transfer_request
from src.services.transfer_request.transfer_request_models import TRANSFER_REQUEST_TEMPLATE_DETAILS
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    # TODO: брать вместо AMOUNT актуальную сумму из письма банка
    amount = args.amount or EnvVar.get_required_env("INVOICE_AMOUNT")
    if not amount:
        parser.error("Pass --amount or set INVOICE_AMOUNT in .env")

    if not args.template.exists():
        LOGGER.error("Transfer Request template not found: %s", args.template)
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
    generate_transfer_request(
        template_path=args.template,
        output_pdf_path=output_pdf_path,
        data=data,
        transfer_request_details=TRANSFER_REQUEST_TEMPLATE_DETAILS,
    )

    LOGGER.info("Transfer Request saved to %s", output_pdf_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate salary invoice PDF and DOCX files.",
    )
    parser.add_argument(
        "--amount",
        help="Transfer Request amount in EUR. Defaults to INVOICE_AMOUNT from .env.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=TransferRequest.TEMPLATE_PATH,
        help=f"Path to invoice DOCX template. Defaults to {TransferRequest.TEMPLATE_PATH}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=TransferRequest.OUTPUT_DIR,
        help=f"Directory for generated files. Defaults to {TransferRequest.OUTPUT_DIR}.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
