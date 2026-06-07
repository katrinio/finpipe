"""Fallback-рендерер transfer request без DOCX-шаблона."""

import logging
from pathlib import Path

from src.services.document.fallback_pdf_renderer import FallbackPdfRenderer

LOGGER = logging.getLogger(__name__)
PdfData = dict[str, str]


class TransferRequestFallbackPdfRenderer(FallbackPdfRenderer):
    """Строит упрощённый PDF transfer request из строковых полей."""

    @classmethod
    def render(cls, output_path: Path, data: PdfData) -> None:
        """Рендерит запасной PDF transfer request."""

        LOGGER.info("Rendering fallback transfer request PDF: %s", output_path)
        cls.render_lines(
            output_path=output_path,
            title="TRANSFER REQUEST",
            lines=cls.build_lines(data),
            pdf_title="Transfer request",
        )

    @classmethod
    def build_lines(cls, data: PdfData) -> list[str]:
        """Преобразует поля transfer request в строки для PDF."""

        return [
            f"Account number: {data['account_number']}",
            f"Date: {data['date']}",
            f"City: {data['city']}",
            f"Name: {data['name']}",
            f"Amount: EUR {data['amount']}",
        ]
