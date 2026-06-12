"""Fallback-рендерер Conversion Order без DOCX-шаблона."""

import logging
from pathlib import Path

from src.infrastructure.document.fallback_pdf_renderer import FallbackPdfRenderer

LOGGER = logging.getLogger(__name__)
PdfData = dict[str, str]


class ConversionOrderFallbackPdfRenderer(FallbackPdfRenderer):
    """Строит упрощённый PDF Conversion Order из строковых полей."""

    @classmethod
    def render(cls, output_path: Path, data: PdfData) -> None:
        """Рендерит запасной PDF Conversion Order."""

        LOGGER.info("Rendering fallback conversion order PDF: %s", output_path)
        cls.render_lines(
            output_path=output_path,
            title="CONVERSION ORDER",
            lines=cls.build_lines(data),
            pdf_title="Conversion order",
        )

    @classmethod
    def build_lines(cls, data: PdfData) -> list[str]:
        """Преобразует поля Conversion Order в строки для PDF."""

        return [
            f"Account number: {data['account_number']}",
            f"Date: {data['date']}",
            f"City: {data['city']}",
            f"Name: {data['name']}",
            f"Amount: EUR {data['amount']}",
        ]
