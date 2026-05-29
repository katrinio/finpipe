import logging
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from src.constants import Format
from src.services.document.docx_to_pdf_converter import PdfConverter

LOGGER = logging.getLogger(__name__)


def generate_transfer_request(
    template_path: Path,
    output_pdf_path: Path,
    data: dict[str, str],
    transfer_request_details,
) -> None:
    LOGGER.info("Rendering transfer request from template: %s", template_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    rendered_docx_path = output_pdf_path.with_suffix(f".{Format.DOCX}")

    render_docx_template(
        template_path=template_path,
        output_path=rendered_docx_path,
        data=data,
        transfer_request_details=transfer_request_details,
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


def render_docx_template(
    template_path: Path,
    output_path: Path,
    data: dict[str, str],
    transfer_request_details,
) -> None:
    LOGGER.info("Rendering transfer request DOCX: %s", output_path)
    replacements = build_replacements(
        data=data,
        transfer_request_details=transfer_request_details,
    )

    with (
        ZipFile(template_path, "r") as source,
        ZipFile(output_path, "w", compression=ZIP_DEFLATED) as target,
    ):
        for name in source.namelist():
            content = source.read(name)

            if name.endswith(".xml"):
                text = content.decode("utf-8")

                for placeholder, value in replacements.items():
                    text = text.replace(placeholder, value)

                content = text.encode("utf-8")

            target.writestr(name, content)


def build_replacements(
    data: dict[str, str],
    transfer_details,
) -> dict[str, str]:
    replacements: dict[str, str] = {}

    for field_name, placeholder_names in transfer_details.placeholder_aliases.items():
        value = str(data[field_name])

        for placeholder_name in placeholder_names:
            placeholder = placeholder_name if placeholder_name.startswith("{{") else f"{{{{{placeholder_name}}}}}"

            replacements[placeholder] = value

    return replacements
