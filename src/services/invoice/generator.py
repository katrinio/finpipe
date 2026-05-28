import logging
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

LOGGER = logging.getLogger(__name__)

PAGES_APP_PATH = Path("/Applications/Pages.app")

PAGES_OPEN_WAIT_ATTEMPTS = 120
PAGES_OPEN_WAIT_SECONDS = 0.5
PAGES_EXPORT_TIMEOUT_SECONDS = 90

FALLBACK_TITLE_Y = 60
FALLBACK_BODY_START_Y = 120
FALLBACK_LINE_STEP = 24


def generate_invoice(
    template_path: Path,
    output_pdf_path: Path,
    data: dict[str, str],
    invoice_details,
) -> None:
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    rendered_docx_path = output_pdf_path.with_suffix(".docx")

    render_docx_template(
        template_path=template_path,
        output_path=rendered_docx_path,
        data=data,
        invoice_details=invoice_details,
    )

    render_invoice_pdf(
        rendered_docx_path=rendered_docx_path,
        output_path=output_pdf_path,
        data=data,
    )

    LOGGER.info(
        "Generated invoice: docx=%s pdf=%s",
        rendered_docx_path,
        output_pdf_path,
    )


def render_docx_template(
    template_path: Path,
    output_path: Path,
    data: dict[str, str],
    invoice_details,
) -> None:
    replacements = build_replacements(
        data=data,
        invoice_details=invoice_details,
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


def render_invoice_pdf(
    rendered_docx_path: Path,
    output_path: Path,
    data: dict[str, str],
) -> None:
    try:
        render_invoice_pdf_with_pages(
            rendered_docx_path=rendered_docx_path,
            output_path=output_path,
        )
    except Exception as error:
        e = error
        LOGGER.warning(
            "Pages export failed, using fallback PDF renderer: %s",
            e,
        )
        render_invoice_pdf_fallback(
            output_path=output_path,
            data=data,
        )


def render_invoice_pdf_with_pages(
    rendered_docx_path: Path,
    output_path: Path,
) -> None:
    if not PAGES_APP_PATH.exists():
        msg = "Pages.app not found"
        raise FileNotFoundError(msg)

    if output_path.exists():
        output_path.unlink()

    subprocess.run(
        ["open", "-a", "Pages", str(rendered_docx_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    script_lines = build_pages_export_script(
        rendered_docx_path=rendered_docx_path,
        output_path=output_path,
    )

    osascript_command = build_osascript_command(script_lines)

    subprocess.run(
        osascript_command,
        check=True,
        capture_output=True,
        text=True,
        timeout=PAGES_EXPORT_TIMEOUT_SECONDS,
    )

    if not output_path.exists():
        msg = "Pages did not create PDF"
        raise RuntimeError(msg)

    if output_path.stat().st_size == 0:
        msg = "Generated PDF is empty"
        raise RuntimeError(msg)


def build_pages_export_script(
    rendered_docx_path: Path,
    output_path: Path,
) -> list[str]:
    return [
        'tell application "Pages"',
        "activate",
        f'open POSIX file "{rendered_docx_path}"',
        "delay 2",
        "set docRef to front document",
        f'export docRef to POSIX file "{output_path}" as PDF',
        "close docRef saving no",
        "end tell",
    ]


def build_osascript_command(script_lines: list[str]) -> list[str]:
    command = ["osascript"]

    for line in script_lines:
        command.extend(["-e", line])

    return command


def render_invoice_pdf_fallback(
    output_path: Path,
    data: dict[str, str],
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=A4)

    _, height = A4

    pdf.setTitle(f"Invoice {data['invoice_number']}")

    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(40, height - FALLBACK_TITLE_Y, "INVOICE")

    pdf.setFont("Helvetica", 12)

    lines = [
        f"Invoice number: {data['invoice_number']}",
        f"Date: {data['date']}",
        f"Period: {data['period_from']} - {data['period_to']}",
        f"Amount: EUR {data['amount']}",
    ]

    y_position = height - FALLBACK_BODY_START_Y

    for line in lines:
        pdf.drawString(40, y_position, line)
        y_position -= FALLBACK_LINE_STEP

    pdf.setFont("Helvetica", 10)

    pdf.drawString(
        40,
        y_position - 20,
        "Generated automatically from invoice template.",
    )
    pdf.save()


def build_replacements(
    data: dict[str, str],
    invoice_details,
) -> dict[str, str]:
    replacements: dict[str, str] = {}

    for field_name, placeholder_names in invoice_details.placeholder_aliases.items():
        value = str(data[field_name])

        for placeholder_name in placeholder_names:
            placeholder = (
                placeholder_name
                if placeholder_name.startswith("{{")
                else f"{{{{{placeholder_name}}}}}"
            )

            replacements[placeholder] = value

    return replacements
