"""Шаг workflow для генерации Bank Confirmation."""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from src.constants import Dir, Format
from src.logging_config import configure_logging
from src.services.bank.bank_confirmation import generate_bank_confirmation_pdf
from src.services.bank.bank_extract import extract_amount
from src.services.bank.exceptions import BankPdfValidationError
from src.services.invoice.context import build_invoice_period
from src.storage.orm.system.document_generation_history import DocumentGenerationHistory, DocumentGenerationStatus, DocumentType
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils.credentials import EnvVar
from src.utils.utils import Utils

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Создаёт CLI-парсер для генерации Bank Confirmation."""

    parser = argparse.ArgumentParser(description="Extract amount and generate bank confirmation.")
    parser.add_argument(
        "--telegram-id",
        type=int,
        required=True,
        help="Telegram user ID whose stored bank details should be used.",
    )
    parser.add_argument(
        "--bank-template",
        type=Path,
        default=None,
        help=f"Path to source bank confirmation PDF. Defaults to the newest PDF in {Dir.ATTACHMENTS}.",
    )
    parser.add_argument("--signature", type=Path, default=Dir.SIGNATURE_ENC)
    parser.add_argument(
        "--without-signature",
        action="store_true",
        help="Generate bank confirmation without signature image.",
    )
    parser.add_argument("--output-dir", type=Path, default=Dir.BANK_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI-точка входа для генерации Bank Confirmation."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        generate_bank_confirmation(
            telegram_id=args.telegram_id,
            bank_template=args.bank_template,
            signature=args.signature,
            output_dir=args.output_dir,
            include_signature=not args.without_signature,
        )
    except Exception:
        LOGGER.exception("Bank confirmation generation failed")
        return 1
    else:
        return 0


def generate_bank_confirmation(
    telegram_id: int,
    bank_template: Path | None = None,
    signature: Path | None = Dir.SIGNATURE_ENC,
    output_dir: Path = Dir.BANK_OUTPUT_DIR,
    include_signature: bool | None = None,
    amount: float | None = None,
) -> Path:
    """Генерирует Bank Confirmation и возвращает путь к созданному файлу."""

    document_number: str | None = None
    LOGGER.info("Document generation started type=%s document=%s telegram_id=%s", DocumentType.BANK_CONFIRMATION, document_number, telegram_id)

    try:
        bank_template = resolve_bank_template(bank_template)
        output_dir.mkdir(parents=True, exist_ok=True)

        LOGGER.info("Preparing bank confirmation from %s", bank_template)
        amount = amount or extract_amount(bank_template)
        bank_details = BankDetails.get_by_owner(telegram_id)
        if bank_details is None:
            msg = "Банковские реквизиты не настроены. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)
        company_profile = CompanyProfile.get_by_owner(telegram_id)
        if company_profile is None:
            msg = "Компания не настроена. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        invoice_period = build_invoice_period()
        period_suffix = Utils.today()
        bank_output = output_dir / f"Obavestenje-o-prilivu-{period_suffix}.{Format.PDF}"

        resolved_signature = resolve_signature(signature)

        generate_bank_confirmation_pdf(
            input_pdf=bank_template,
            output_pdf=bank_output,
            amount=amount,
            date=invoice_period.invoice_date,
            company_profile=company_profile,
            bank_details=bank_details,
            signature=resolved_signature,
        )
    except Exception as error:
        DocumentGenerationHistory.add_attempt(
            document_type=DocumentType.BANK_CONFIRMATION,
            document_number=document_number,
            telegram_id=telegram_id,
            status=DocumentGenerationStatus.FAILED,
            error_message=str(error),
        )
        LOGGER.warning("Document generation failed type=%s document=%s telegram_id=%s", DocumentType.BANK_CONFIRMATION, document_number, telegram_id)
        raise

    DocumentGenerationHistory.add_attempt(
        document_type=DocumentType.BANK_CONFIRMATION,
        document_number=document_number,
        telegram_id=telegram_id,
        status=DocumentGenerationStatus.SUCCESS,
        error_message=None,
    )
    LOGGER.info("Document generation succeeded type=%s document=%s telegram_id=%s", DocumentType.BANK_CONFIRMATION, document_number, telegram_id)
    LOGGER.info("Bank confirmation saved to %s", bank_output)
    return bank_output


def resolve_bank_template(bank_template: Path | None) -> Path:
    """Определяет, какой исходный PDF использовать для Bank Confirmation."""

    if bank_template is not None:
        if not bank_template.exists():
            msg = f"Bank confirmation source PDF not found: {bank_template}"
            raise BankPdfValidationError(msg)

        if not is_pdf_file(bank_template):
            msg = f"Bank confirmation template is not a PDF: {bank_template}"
            raise BankPdfValidationError(msg)

        LOGGER.info("Using bank confirmation source PDF from --bank-template: %s", bank_template)
        return bank_template

    if not Dir.ATTACHMENTS.exists():
        msg = f"Attachments directory not found: {Dir.ATTACHMENTS}"
        raise BankPdfValidationError(msg)

    candidates = [path for path in Dir.ATTACHMENTS.iterdir() if path.is_file() and is_pdf_file(path)]
    if not candidates:
        msg = f"No bank confirmation PDF found in {Dir.ATTACHMENTS}. Pass --bank-template."
        raise BankPdfValidationError(msg)

    newest_pdf = max(candidates, key=lambda path: path.stat().st_mtime)
    LOGGER.info("Using newest bank confirmation PDF from %s: %s", Dir.ATTACHMENTS, newest_pdf)
    return newest_pdf


def is_pdf_file(path: Path) -> bool:
    """Проверяет PDF по сигнатуре файла, а не только по расширению."""

    with path.open("rb") as file_handle:
        return file_handle.read(5) == b"%PDF-"


def resolve_signature(signature: Path | None) -> Path | None:
    """Возвращает путь к подписи или None."""

    return signature


if __name__ == "__main__":
    raise SystemExit(main())
