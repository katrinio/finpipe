"""Шаг workflow для генерации инвойса."""

import argparse
import logging
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from src.constants import Dir, Format
from src.logging_config import configure_logging
from src.services.invoice.context import build_invoice_period
from src.services.invoice.generate import generate_invoice
from src.services.invoice.models import InvoiceData
from src.storage.orm import HistoryRecord, InvoiceGenerationStatus, UserConfig
from src.storage.orm.user.bank_details import BankDetails
from src.storage.orm.user.company_profile import CompanyProfile
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)
DEFAULT_SERVICE_AGREEMENT_DATE = "01.05.2025"


def generate_invoice_pdf(
    telegram_id: int,
    invoice_date: date | None = None,
    template_path: Path = Dir.INVOICE_TEMPLATE,
    output_dir: Path = Dir.INVOICE_OUTPUT_DIR,
) -> Path:
    """Генерирует Invoice и пишет в БД результат каждой попытки."""

    invoice_period = build_invoice_period(invoice_date)
    invoice_number = invoice_period.invoice_number
    output_pdf_path = output_dir / f"invoice-{invoice_number}.{Format.PDF}"

    if HistoryRecord.has_attempts(invoice_number):
        LOGGER.info("Invoice regeneration requested for invoice_number=%s telegram_id=%s", invoice_number, telegram_id)

    LOGGER.info("Invoice generation started for invoice_number=%s telegram_id=%s", invoice_number, telegram_id)

    try:
        config = UserConfig.get_by_owner(telegram_id)
        if config is None or config.invoice_amount is None:
            msg = "Сумма Invoice не указана. Используйте «💰 Указать сумму»."
            raise ValueError(msg)

        company_profile = CompanyProfile.get_by_owner(telegram_id)
        if company_profile is None:
            msg = "Компания не настроена. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        bank_details = BankDetails.get_by_owner(telegram_id)
        if bank_details is None:
            msg = "Банковские реквизиты не настроены. Загрузите профиль через раздел «Профиль»."
            raise ValueError(msg)

        invoice_data = InvoiceData(
            account_holder=bank_details.account_holder,
            account_holder_address=bank_details.account_holder_address or "",
            account_bic=bank_details.bic,
            account_iban=bank_details.iban,
            account_number=bank_details.account_number,
            amount=str(config.invoice_amount),
            bank_name=bank_details.bank_name,
            company_address=company_profile.company_address,
            company_name=company_profile.company_name,
            date_from=invoice_period.period_from,
            date_to=invoice_period.period_to,
            invoice_date=invoice_period.invoice_date,
            invoice_number=invoice_number,
            service_agreement_date=(
                company_profile.service_agreement_date.strftime("%d.%m.%Y")
                if company_profile.service_agreement_date is not None
                else DEFAULT_SERVICE_AGREEMENT_DATE
            ),
        )

        generate_invoice(
            template_path=template_path,
            output_pdf_path=output_pdf_path,
            data=invoice_data,
        )
    except Exception as error:
        HistoryRecord.add_attempt(
            invoice_number=invoice_number,
            telegram_id=telegram_id,
            status=InvoiceGenerationStatus.FAILED,
            error_message=str(error),
        )
        LOGGER.warning("Invoice generation failed for invoice_number=%s telegram_id=%s", invoice_number, telegram_id)
        raise

    HistoryRecord.add_attempt(
        invoice_number=invoice_number,
        telegram_id=telegram_id,
        status=InvoiceGenerationStatus.SUCCESS,
        error_message=None,
    )
    LOGGER.info("Invoice generation succeeded for invoice_number=%s telegram_id=%s", invoice_number, telegram_id)
    return output_pdf_path


def main(argv: Sequence[str] | None = None) -> int:
    """CLI-точка входа для генерации инвойса."""

    configure_logging()
    EnvVar.get_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.template.exists():
        LOGGER.error("Invoice template not found: %s", args.template)
        return 1

    invoice_period = build_invoice_period(args.invoice_date)

    LOGGER.info(
        "Generating invoice %s for period %s - %s",
        invoice_period.invoice_number,
        invoice_period.period_from,
        invoice_period.period_to,
    )
    pdf_path = generate_invoice_pdf(
        telegram_id=args.telegram_id,
        invoice_date=args.invoice_date,
        template_path=args.template,
        output_dir=args.output_dir,
    )

    LOGGER.info("Invoice saved to %s", pdf_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Создаёт CLI-парсер для генерации инвойса."""

    parser = argparse.ArgumentParser(
        description="Generate salary invoice PDF and DOCX files.",
    )
    parser.add_argument(
        "--telegram-id",
        type=int,
        required=True,
        help="Telegram user ID whose stored invoice amount should be used.",
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
        default=Dir.INVOICE_TEMPLATE,
        help=f"Path to invoice DOCX template. Defaults to {Dir.INVOICE_TEMPLATE}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Dir.INVOICE_OUTPUT_DIR,
        help=f"Directory for generated files. Defaults to {Dir.INVOICE_OUTPUT_DIR}.",
    )
    return parser


def parse_invoice_date(value: str) -> date:
    """Преобразует строку CLI в дату инвойса."""

    try:
        return date.fromisoformat(value)
    except ValueError as error:
        msg = "Expected date in YYYY-MM-DD format"
        raise argparse.ArgumentTypeError(msg) from error


if __name__ == "__main__":
    raise SystemExit(main())
