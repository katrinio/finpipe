import logging
from pathlib import Path

from src.constants import Format
from src.services.document.docx_template_renderer import DocxTemplateRenderer
from src.services.document.docx_to_pdf_converter import PdfConverter
from src.workflows.generate_transfer_request import TransferRequestTemplateDetails

LOGGER = logging.getLogger(__name__)


def generate_transfer_request(
    template_path: Path,
    output_pdf_path: Path,
    data: dict[str, str],
    transfer_request_details: TransferRequestTemplateDetails,
) -> None:
    LOGGER.info("Rendering transfer request from template: %s", template_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_docx_path = output_pdf_path.with_suffix(f".{Format.DOCX}")

    replacements = build_replacements(data=data, transfer_request_details=transfer_request_details)

    DocxTemplateRenderer.render(
        template_path=template_path,
        output_path=rendered_docx_path,
        replacements=replacements,
    )

    PdfConverter.render_transfer_pdf(
        rendered_docx_path=rendered_docx_path,
        output_path=output_pdf_path,
        data=data,
    )

    LOGGER.info(
        "Generated transfer: docx=%s pdf=%s",
        rendered_docx_path,
        output_pdf_path,
    )


def build_replacements(data: dict[str, str], transfer_request_details: TransferRequestTemplateDetails) -> dict[str, str]:
    replacements: dict[str, str] = {}

    for field_name, placeholder_names in transfer_request_details.placeholder_aliases.items():
        value = str(data[field_name])

        for placeholder_name in placeholder_names:
            placeholder = placeholder_name if placeholder_name.startswith("{{") else f"{{{{{placeholder_name}}}}}"

            replacements[placeholder] = value

    return replacements
