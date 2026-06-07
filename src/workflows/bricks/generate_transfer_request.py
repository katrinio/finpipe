"""Шаг workflow для генерации transfer request."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from src.constants import Dir, Format
from src.logging_config import configure_logging
from src.services.invoice.context import build_invoice_period
from src.services.transfer_request.generate import generate_transfer_request
from src.services.transfer_request.models import TransferRequestData
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def generate_transfer_request_pdf(
    amount: str,
    invoice_date: date | None = None,
    template_path: Path = Dir.TRANSFER_REQUEST_TEMPLATE,
    output_dir: Path = Dir.TRANSFER_REQUEST_OUTPUT_DIR,
) -> Path:
    """
    Генерирует transfer request на указанную сумму
    и возвращает путь к PDF.
    """

    invoice_period = build_invoice_period(invoice_date)
    output_pdf_path = output_dir / f"transfer-request-{invoice_period.invoice_number}.{Format.PDF}"

    transfer_request_data = TransferRequestData(
        account_number=EnvVar.get_required_env("ACCOUNT_NUMBER"),
        amount=amount,
        city=EnvVar.get_required_env("CITY"),
        date=invoice_period.invoice_date,
        name=EnvVar.get_required_env("ACCOUNT_HOLDER"),
    )

    generate_transfer_request(
        template_path=template_path,
        output_pdf_path=output_pdf_path,
        data=transfer_request_data,
    )
    return output_pdf_path


def main(argv: Sequence[str] | None = None) -> int:
    """CLI-точка входа для генерации transfer request."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    amount = args.amount or EnvVar.get_required_env("INVOICE_AMOUNT")

    if not args.template.exists():
        LOGGER.error("Transfer Request template not found: %s", args.template)
        return 1

    invoice_period = build_invoice_period(args.invoice_date)
    LOGGER.info(
        "Generating transfer request %s for period %s - %s",
        invoice_period.invoice_number,
        invoice_period.period_from,
        invoice_period.period_to,
    )
    output_pdf_path = generate_transfer_request_pdf(
        amount=amount,
        invoice_date=args.invoice_date,
        template_path=args.template,
        output_dir=args.output_dir,
    )

    LOGGER.info("Transfer Request saved to %s", output_pdf_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Создаёт CLI-парсер для генерации transfer request."""

    parser = argparse.ArgumentParser(
        description="Generate salary invoice PDF and DOCX files.",
    )
    parser.add_argument(
        "--amount",
        help="Transfer Request amount in EUR. Defaults to INVOICE_AMOUNT from .env.",
    )
    parser.add_argument(
        "--date",
        dest="invoice_date",
        type=parse_invoice_date,
        default=None,
        help="Transfer Request date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Dir.TRANSFER_REQUEST_TEMPLATE,
        help=f"Path to invoice DOCX template. Defaults to {Dir.TRANSFER_REQUEST_TEMPLATE}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Dir.TRANSFER_REQUEST_OUTPUT_DIR,
        help=f"Directory for generated files. Defaults to {Dir.TRANSFER_REQUEST_OUTPUT_DIR}.",
    )
    return parser


def parse_invoice_date(value: str) -> date:
    """Преобразует строку CLI в дату документа."""

    try:
        return date.fromisoformat(value)
    except ValueError as error:
        msg = "Expected date in YYYY-MM-DD format"
        raise argparse.ArgumentTypeError(msg) from error


if __name__ == "__main__":
    raise SystemExit(main())
