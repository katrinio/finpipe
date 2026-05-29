import argparse
import logging
from pathlib import Path

from services.bank.extract import extract_amount
from services.bank.fill import fill_bank_pdf
from services.constants import Bank
from services.invoice.context import build_invoice_period

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract amount and fill bank PDF.")
    parser.add_argument("--bank-template", type=Path, default=Bank.TEMPLATE_PATH)
    parser.add_argument("--signature", type=Path, default=Bank.SIGNATURE_PATH)
    parser.add_argument("--output-dir", type=Path, default=Bank.OUTPUT_DIR)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return run(args.bank_template, args.signature, args.output_dir)
    except Exception as error:
        e = error
        LOGGER.exception("Bank PDF processing failed: %s", e)
        return 1


def run(bank_template: Path, signature: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)

    amount = extract_amount(bank_template)
    invoice_period = build_invoice_period()
    # period_suffix = build_period_suffix(invoice_period.invoice_number)
    bank_output = output_dir / "bank_8.pdf"

    fill_bank_pdf(
        input_pdf=bank_template,
        output_pdf=bank_output,
        amount=amount,
        date=invoice_period.date,
        signature=signature,
    )

    LOGGER.info("Bank PDF processing finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
