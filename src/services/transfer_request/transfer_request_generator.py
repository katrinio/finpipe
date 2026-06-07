"""Генерация transfer request из DOCX-шаблона с fallback на простой PDF."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

from src.constants import Dir, Format
from src.infrastructure.document.docx_template_renderer import DocxTemplateRenderer
from src.infrastructure.document.docx_to_pdf_converter import DocxToPdfConverter
from src.infrastructure.document.replacement import Replacement
from src.services.transfer_request.transfer_request_models import TransferRequestData
from src.services.transfer_request.transfer_request_pdf_renderer import TransferRequestFallbackPdfRenderer
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def generate_transfer_request(
    data: TransferRequestData | Mapping[str, object],
    template_path: Path = Dir.TRANSFER_REQUEST_TEMPLATE,
    output_pdf_path: Path = Dir.TRANSFER_REQUEST_OUTPUT_DIR,
) -> Path:
    """Генерирует transfer request и возвращает путь к PDF."""

    template_path = resolve_project_path(template_path)
    output_pdf_path = resolve_project_path(output_pdf_path)
    LOGGER.info("Rendering transfer request from template: %s", template_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_docx_path = output_pdf_path.with_suffix(f".{Format.DOCX}")

    template_data = Replacement.to_template_data(data)
    replacements = Replacement.build_replacements(template_data)
    pdf_data = {field_name: str(value) for field_name, value in template_data.items()}

    if not template_path.exists():
        # В CI шаблон может отсутствовать, но сам workflow должен завершаться успешно.
        LOGGER.warning(
            "Transfer request template not found before DOCX render, using fallback PDF renderer: %s",
            template_path,
        )
        TransferRequestFallbackPdfRenderer.render(output_pdf_path, pdf_data)
        LOGGER.info(
            "Generated transfer via fallback only: pdf=%s",
            output_pdf_path,
        )
        return output_pdf_path

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
        LOGGER.warning(
            "Transfer request template not found, using fallback PDF renderer: %s",
            error,
        )
        TransferRequestFallbackPdfRenderer.render(output_pdf_path, pdf_data)

    LOGGER.info(
        "Generated transfer: docx=%s pdf=%s",
        rendered_docx_path,
        output_pdf_path,
    )

    return output_pdf_path


def render_pdf(rendered_docx_path: Path, output_path: Path, data: dict[str, str]) -> None:
    """Пытается сконвертировать DOCX в PDF, иначе включает fallback."""

    try:
        DocxToPdfConverter.convert(
            rendered_docx_path=rendered_docx_path,
            output_path=output_path,
        )
    except Exception as error:
        LOGGER.warning(
            "DOCX transfer request PDF conversion failed, using fallback renderer: %s",
            error,
        )
        TransferRequestFallbackPdfRenderer.render(output_path, data)


def resolve_project_path(path: Path) -> Path:
    """Резолвит относительный путь от корня проекта."""

    if path.is_absolute():
        return path

    return EnvVar.PROJECT_ROOT / path
