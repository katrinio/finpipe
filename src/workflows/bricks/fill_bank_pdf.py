import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from src.constants import Dir, Format
from src.logging_config import configure_logging
from src.services.bank.bank_extract import extract_amount
from src.services.bank.bank_fill import fill_bank_pdf as render_bank_pdf
from src.services.invoice.invoice_context import build_invoice_period
from src.utils.credentials import EnvVar
from src.utils.utils import Utils

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract amount and fill bank PDF.")
    parser.add_argument(
        "--bank-template",
        type=Path,
        default=None,
        help=f"Path to source bank PDF. Defaults to the newest PDF in {Dir.ATTACHMENTS}.",
    )
    parser.add_argument("--signature", type=Path, default=Dir.SIGNATURE_PATH)
    parser.add_argument("--output-dir", type=Path, default=Dir.BANK_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        fill_bank_pdf_with_data(args.bank_template, args.signature, args.output_dir)
    except Exception:
        LOGGER.exception("Bank PDF processing failed")
        return 1
    else:
        return 0


def fill_bank_pdf_with_data(
    bank_template: Path | None = None,
    signature: Path = Dir.SIGNATURE_PATH,
    output_dir: Path = Dir.BANK_OUTPUT_DIR,
) -> Path:
    bank_template = resolve_bank_template(bank_template)
    output_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Preparing bank PDF from %s", bank_template)
    amount = extract_amount(bank_template)
    invoice_period = build_invoice_period()
    period_suffix = Utils.today()
    bank_output = output_dir / f"Obavestenje-o-prilivu-{period_suffix}.{Format.PDF}"

    render_bank_pdf(
        input_pdf=bank_template,
        output_pdf=bank_output,
        amount=amount,
        date=invoice_period.invoice_date,
        signature=signature,
    )

    LOGGER.info("Bank PDF processing finished successfully: %s", bank_output)
    return bank_output


def resolve_bank_template(bank_template: Path | None) -> Path:
    if bank_template is not None:
        if not bank_template.exists():
            msg = f"Bank PDF not found: {bank_template}"
            raise FileNotFoundError(msg)

        if not is_pdf_file(bank_template):
            msg = f"Bank template is not a PDF: {bank_template}"
            raise ValueError(msg)

        LOGGER.info("Using bank PDF from --bank-template: %s", bank_template)
        return bank_template

    if not Dir.ATTACHMENTS.exists():
        msg = f"Attachments directory not found: {Dir.ATTACHMENTS}"
        raise FileNotFoundError(msg)

    candidates = [path for path in Dir.ATTACHMENTS.iterdir() if path.is_file() and is_pdf_file(path)]
    if not candidates:
        msg = f"No bank PDF found in {Dir.ATTACHMENTS}. Pass --bank-template."
        raise FileNotFoundError(msg)

    newest_pdf = max(candidates, key=lambda path: path.stat().st_mtime)
    LOGGER.info("Using newest bank PDF from %s: %s", Dir.ATTACHMENTS, newest_pdf)
    return newest_pdf


def is_pdf_file(path: Path) -> bool:
    with path.open("rb") as file_handle:
        return file_handle.read(5) == b"%PDF-"


if __name__ == "__main__":
    raise SystemExit(main())
