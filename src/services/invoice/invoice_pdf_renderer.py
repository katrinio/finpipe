"""Fallback-рендерер инвойса без использования DOCX-шаблона."""

import logging
from pathlib import Path

from src.infrastructure.document.fallback_pdf_renderer import FallbackPdfRenderer

LOGGER = logging.getLogger(__name__)
PdfData = dict[str, str]


class InvoiceFallbackPdfRenderer(FallbackPdfRenderer):
    """Строит упрощённый PDF-инвойс из набора строк."""

    @classmethod
    def render(cls, output_path: Path, data: PdfData) -> None:
        """Рендерит запасной PDF-инвойс."""

        LOGGER.info("Rendering fallback invoice PDF: %s", output_path)
        cls.render_lines(
            output_path=output_path,
            title="INVOICE",
            lines=cls.build_lines(data),
            pdf_title=f"Invoice {data['invoice_number']}",
        )

    @classmethod
    def build_lines(cls, data: PdfData) -> list[str]:
        """Преобразует поля инвойса в строки для fallback PDF."""

        return [
            f"From: {data['account_holder']}",
            f"From address: {data['account_holder_address']}",
            f"To: {data['company_name']}",
            f"To address: {data['company_address']}",
            f"Invoice number: {data['invoice_number']}",
            f"Invoice date: {data['invoice_date']}",
            f"Period: {data['date_from']} - {data['date_to']}",
            f"Service agreement date: {data['service_agreement_date']}",
            f"Amount: EUR {data['amount']}",
            f"Bank name: {data['bank_name']}",
            f"Account number: {data['account_number']}",
            f"SWIFT/BIC: {data['account_bic']}",
            f"IBAN: {data['account_iban']}",
        ]
