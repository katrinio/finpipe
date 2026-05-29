import argparse
import logging
from pathlib import Path

from src.constants import Bank, Format
from src.services.bank.extract import extract_amount
from src.services.bank.fill import fill_bank_pdf
from src.services.invoice.context import build_invoice_period
from src.utils import Utils

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
    except Exception as e:
        error = e
        LOGGER.exception("Bank PDF processing failed: %s", error)
        return 1


def run(bank_template: Path, signature: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)

    amount = extract_amount(bank_template)
    invoice_period = build_invoice_period()
    period_suffix = Utils.today()
    bank_output = output_dir / f"Obavestenje-o-prilivu-{period_suffix}.{Format.PDF}"

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
