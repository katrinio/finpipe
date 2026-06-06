from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

from src.constants import Dir, Format
from src.services.document.docx_template_renderer import DocxTemplateRenderer
from src.services.document.docx_to_pdf_converter import DocxToPdfConverter
from src.services.document.replacement import Replacement
from src.services.transfer_request.transfer_request_models import TransferRequestData
from src.services.transfer_request.transfer_request_pdf_renderer import TransferRequestFallbackPdfRenderer

LOGGER = logging.getLogger(__name__)


def generate_transfer_request(
    data: TransferRequestData | Mapping[str, object],
    template_path: Path = Dir.TRANSFER_REQUEST_TEMPLATE,
    output_pdf_path: Path = Dir.TRANSFER_REQUEST_OUTPUT_DIR,
) -> Path:
    LOGGER.info("Rendering transfer request from template: %s", template_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_docx_path = output_pdf_path.with_suffix(f".{Format.DOCX}")

    template_data = Replacement.to_template_data(data)
    replacements = Replacement.build_replacements(template_data)
    pdf_data = {field_name: str(value) for field_name, value in template_data.items()}

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

    LOGGER.info(
        "Generated transfer: docx=%s pdf=%s",
        rendered_docx_path,
        output_pdf_path,
    )

    return output_pdf_path


def render_pdf(rendered_docx_path: Path, output_path: Path, data: dict[str, str]) -> None:
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
