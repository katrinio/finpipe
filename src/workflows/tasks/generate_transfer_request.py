"""Шаг workflow для генерации transfer request."""

import argparse
import logging
from collections.abc import Sequence
from datetime import date
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from src.constants import Dir, Format
from src.infrastructure.document.pdf_get_page_size import PdfGetPageSize
from src.infrastructure.document.sign_pdf import PdfSigner
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.logging_config import configure_logging
from src.services.invoice.context import build_invoice_period
from src.services.signing.context import SignaturePositions
from src.services.transfer_request.generate import generate_transfer_request
from src.services.transfer_request.models import TransferRequestData
from src.storage.orm import DocumentGenerationHistory, DocumentGenerationStatus, DocumentType
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def generate_transfer_request_pdf(
    telegram_id: int,
    amount: str,
    invoice_date: date | None = None,
    template_path: Path = Dir.TRANSFER_REQUEST_TEMPLATE,
    output_dir: Path = Dir.TRANSFER_REQUEST_OUTPUT_DIR,
    signature: Path | None = Dir.SIGNATURE_ENC,
) -> Path:
    """
    Генерирует transfer request на указанную сумму
    и возвращает путь к PDF.
    """

    invoice_period = build_invoice_period(invoice_date)
    document_number = f"TR-{invoice_period.invoice_number}"
    output_pdf_path = output_dir / f"transfer-request-{invoice_period.invoice_number}.{Format.PDF}"

    LOGGER.info("Document generation started type=%s document=%s telegram_id=%s", DocumentType.CONVERSION_ORDER, document_number, telegram_id)

    try:
        bank_details = BankDetails.get_by_owner(telegram_id)
        if bank_details is None:
            msg = "Банковские реквизиты не настроены. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        company_profile = CompanyProfile.get_by_owner(telegram_id)
        if company_profile is None:
            msg = "Компания не настроена. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        transfer_request_data = TransferRequestData(
            account_number=bank_details.account_number,
            amount=amount,
            city=company_profile.city or "",
            date=invoice_period.invoice_date,
            name=bank_details.account_holder,
        )

        generate_transfer_request(
            template_path=template_path,
            output_pdf_path=output_pdf_path,
            data=transfer_request_data,
        )
        apply_signature_to_pdf(output_pdf_path, signature)
    except Exception as error:
        DocumentGenerationHistory.add_attempt(
            document_type=DocumentType.CONVERSION_ORDER,
            document_number=document_number,
            telegram_id=telegram_id,
            status=DocumentGenerationStatus.FAILED,
            error_message=str(error),
        )
        LOGGER.warning("Document generation failed type=%s document=%s telegram_id=%s", DocumentType.CONVERSION_ORDER, document_number, telegram_id)
        raise

    DocumentGenerationHistory.add_attempt(
        document_type=DocumentType.CONVERSION_ORDER,
        document_number=document_number,
        telegram_id=telegram_id,
        status=DocumentGenerationStatus.SUCCESS,
        error_message=None,
    )
    LOGGER.info("Document generation succeeded type=%s document=%s telegram_id=%s", DocumentType.CONVERSION_ORDER, document_number, telegram_id)
    return output_pdf_path


def main(argv: Sequence[str] | None = None) -> int:
    """CLI-точка входа для генерации transfer request."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    amount = args.amount
    if amount is None:
        LOGGER.error("Transfer Request amount is not provided")
        return 1

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
        telegram_id=args.telegram_id,
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
        "--telegram-id",
        type=int,
        required=True,
        help="Telegram user ID whose stored bank details should be used.",
    )
    parser.add_argument(
        "--amount",
        help="Transfer Request amount in EUR.",
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


def apply_signature_to_pdf(output_pdf_path: Path, signature: Path | None) -> None:
    """Накладывает подпись на уже сгенерированный PDF transfer request."""

    if signature is None:
        LOGGER.info("Transfer request signature is disabled")
        return

    if not signature.exists():
        LOGGER.warning("Transfer request signature image does not exist: %s", signature)
        return

    reader = PdfReader(str(output_pdf_path))
    page = reader.pages[0]

    packet = BytesIO()
    overlay = canvas.Canvas(packet, pagesize=PdfGetPageSize.get_page_size(page))
    signature_bytes = SignatureCipher.decrypt_bytes(signature)
    PdfSigner.draw_signature(
        pdf_canvas=overlay,
        signature=signature_bytes,
        position=SignaturePositions.TRANSFER_REQUEST,
    )
    overlay.save()
    packet.seek(0)

    overlay_page = PdfReader(packet).pages[0]
    page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(page)
    for other_page in reader.pages[1:]:
        writer.add_page(other_page)

    with output_pdf_path.open("wb") as file_handle:
        writer.write(file_handle)


if __name__ == "__main__":
    raise SystemExit(main())
