"""Шаг workflow для генерации Conversion Order."""

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
from src.services.conversion_order.generate import generate_conversion_order
from src.services.conversion_order.models import ConversionOrderData
from src.services.invoice.context import build_invoice_period
from src.services.signing.context import SignaturePositions
from src.storage.orm.system.document_generation_history import DocumentGenerationHistory, DocumentGenerationStatus, DocumentType
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.storage.orm.user.signature import Signature
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def generate_conversion_order_pdf(
    telegram_id: int,
    conversion_amount_eur: float,
    invoice_amount_eur: int | None = None,
    bank_received_amount_eur: float | None = None,
    invoice_date: date | None = None,
    template_path: Path = Dir.CONVERSION_ORDER_TEMPLATE,
    output_dir: Path = Dir.CONVERSION_ORDER_OUTPUT_DIR,
    signature: Path | None = Dir.SIGNATURE_ENC,
) -> Path:
    """Генерирует Conversion Order на указанную сумму и возвращает путь к PDF."""

    invoice_period = build_invoice_period(invoice_date)
    document_number = f"TR-{invoice_period.invoice_number}"
    output_pdf_path = output_dir / f"conversion-order-{invoice_period.invoice_number}.{Format.PDF}"

    LOGGER.info("Document generation started type=%s document=%s telegram_id=%s", DocumentType.CONVERSION_ORDER, document_number, telegram_id)
    LOGGER.info(
        "Preparing transfer request: invoice=%s EUR, received=%s EUR, exchange=%s EUR",
        invoice_amount_eur,
        bank_received_amount_eur,
        conversion_amount_eur,
    )

    try:
        bank_details = BankDetails.get_by_owner(telegram_id)
        if bank_details is None:
            msg = "Банковские реквизиты не настроены. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        company_profile = CompanyProfile.get_by_owner(telegram_id)
        if company_profile is None:
            msg = "Компания не настроена. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        conversion_order_data = ConversionOrderData(
            account_number=bank_details.account_number,
            exchange_amount_eur=format_eur_amount(conversion_amount_eur),
            city=company_profile.city or "",
            date=invoice_period.invoice_date,
            name=bank_details.account_holder,
        )

        LOGGER.info(
            "Rendering transfer request document with exchange amount: %s EUR",
            conversion_amount_eur,
        )
        generate_conversion_order(
            template_path=template_path,
            output_pdf_path=output_pdf_path,
            data=conversion_order_data,
        )
        apply_signature_to_pdf(
            output_pdf_path,
            resolve_signature_for_user(telegram_id, signature),
        )
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
    """CLI-точка входа для генерации Conversion Order."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    amount = args.amount
    if amount is None:
        LOGGER.error("Conversion Order amount is not provided")
        return 1

    if not args.template.exists():
        LOGGER.error("Conversion Order template not found: %s", args.template)
        return 1

    invoice_period = build_invoice_period(args.invoice_date)
    LOGGER.info(
        "Generating conversion order %s for period %s - %s",
        invoice_period.invoice_number,
        invoice_period.period_from,
        invoice_period.period_to,
    )
    output_pdf_path = generate_conversion_order_pdf(
        telegram_id=args.telegram_id,
        conversion_amount_eur=float(amount),
        invoice_date=args.invoice_date,
        template_path=args.template,
        output_dir=args.output_dir,
    )

    LOGGER.info("Conversion Order saved to %s", output_pdf_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Создаёт CLI-парсер для генерации Conversion Order."""

    parser = argparse.ArgumentParser(
        description="Generate conversion order PDF files.",
    )
    parser.add_argument(
        "--telegram-id",
        type=int,
        required=True,
        help="Telegram user ID whose stored bank details should be used.",
    )
    parser.add_argument(
        "--amount",
        help="Conversion Order amount in EUR.",
    )
    parser.add_argument(
        "--date",
        dest="invoice_date",
        type=parse_invoice_date,
        default=None,
        help="Conversion Order date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Dir.CONVERSION_ORDER_TEMPLATE,
        help=f"Path to conversion order DOCX template. Defaults to {Dir.CONVERSION_ORDER_TEMPLATE}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Dir.CONVERSION_ORDER_OUTPUT_DIR,
        help=f"Directory for generated files. Defaults to {Dir.CONVERSION_ORDER_OUTPUT_DIR}.",
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
    """Накладывает подпись на уже сгенерированный PDF Conversion Order."""

    if signature is None:
        LOGGER.info("Conversion order signature is disabled")
        return

    if not signature.exists():
        LOGGER.warning("Conversion order signature image does not exist: %s", signature)
        return

    reader = PdfReader(str(output_pdf_path))
    page = reader.pages[0]

    packet = BytesIO()
    overlay = canvas.Canvas(packet, pagesize=PdfGetPageSize.get_page_size(page))
    signature_bytes = SignatureCipher.decrypt_bytes(signature)
    PdfSigner.draw_signature(
        pdf_canvas=overlay,
        signature=signature_bytes,
        position=SignaturePositions.CONVERSION_ORDER,
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


def resolve_signature_for_user(telegram_id: int, signature: Path | None) -> Path | None:
    """Выбирает подпись для Conversion Order с приоритетом активной подписи пользователя."""

    if signature is None:
        return None

    if signature != Dir.SIGNATURE_ENC:
        return signature

    workflow_signature = Signature.resolve_workflow_signature_path(telegram_id)
    if workflow_signature is not None:
        return workflow_signature

    return signature


def format_eur_amount(value: float) -> str:
    """Форматирует сумму EUR для подстановки в документ."""

    return f"{value:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
