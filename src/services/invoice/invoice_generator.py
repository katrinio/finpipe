"""Генерация инвойса из шаблона с fallback на простой PDF."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

from src.constants import Format
from src.infrastructure.document.docx_template_renderer import DocxTemplateRenderer
from src.infrastructure.document.docx_to_pdf_converter import DocxToPdfConverter
from src.infrastructure.document.replacement import Replacement
from src.services.invoice.invoice_models import InvoiceData
from src.services.invoice.invoice_pdf_renderer import InvoiceFallbackPdfRenderer

LOGGER = logging.getLogger(__name__)


def generate_invoice(
    template_path: Path,
    output_pdf_path: Path,
    data: InvoiceData | Mapping[str, object],
) -> None:
    """Генерирует DOCX и PDF инвойса из переданных данных."""

    LOGGER.info("Rendering invoice from template: %s", template_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_docx_path = output_pdf_path.with_suffix(f".{Format.DOCX}")

    template_data = Replacement.to_template_data(data)
    replacements = Replacement.build_replacements(template_data)
    pdf_data = {field_name: str(value) for field_name, value in template_data.items()}

    try:
        DocxTemplateRenderer.render(
            template_path=template_path,
            output_path=rendered_docx_path,
            replacements=replacements,
        )

        render_pdf(
            rendered_docx_path=rendered_docx_path,
            output_path=output_pdf_path,
            data=pdf_data,
        )
    except FileNotFoundError as error:
        # При отсутствии шаблона сохраняем workflow рабочим через fallback PDF.
        LOGGER.warning(
            "Invoice template not found, using fallback PDF renderer: %s",
            error,
        )
        InvoiceFallbackPdfRenderer.render(output_pdf_path, pdf_data)

    LOGGER.info(
        "Generated invoice: docx=%s pdf=%s",
        rendered_docx_path,
        output_pdf_path,
    )


def render_pdf(rendered_docx_path: Path, output_path: Path, data: dict[str, str]) -> None:
    """Пытается сконвертировать DOCX в PDF, иначе использует fallback."""

    try:
        DocxToPdfConverter.convert(
            rendered_docx_path=rendered_docx_path,
            output_path=output_path,
        )
    except Exception as error:
        LOGGER.warning(
            "DOCX invoice PDF conversion failed, using fallback renderer: %s",
            error,
        )
        InvoiceFallbackPdfRenderer.render(output_path, data)
