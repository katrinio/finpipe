import logging
import subprocess
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

LOGGER = logging.getLogger(__name__)


class PdfConverter:
    PAGES_APP_PATH = Path("/Applications/Pages.app")

    PAGES_OPEN_WAIT_ATTEMPTS = 120
    PAGES_OPEN_WAIT_SECONDS = 0.5
    PAGES_EXPORT_TIMEOUT_SECONDS = 90

    FALLBACK_TITLE_Y = 60
    FALLBACK_BODY_START_Y = 120
    FALLBACK_LINE_STEP = 24

    @classmethod
    def render_invoice_pdf_with_pages(cls, rendered_docx_path: Path, output_path: Path) -> None:
        if not cls.PAGES_APP_PATH.exists():
            msg = "Pages.app not found"
            raise FileNotFoundError(msg)

        if output_path.exists():
            output_path.unlink()

        LOGGER.info("Exporting invoice PDF with Pages: %s", output_path)
        subprocess.run(
            ["open", "-a", "Pages", str(rendered_docx_path)],
            check=True,
            capture_output=True,
            text=True,
        )

        script_lines = cls.build_pages_export_script(
            rendered_docx_path=rendered_docx_path,
            output_path=output_path,
        )

        osascript_command = cls.build_osascript_command(script_lines)

        subprocess.run(
            osascript_command,
            check=True,
            capture_output=True,
            text=True,
            timeout=cls.PAGES_EXPORT_TIMEOUT_SECONDS,
        )

        if not output_path.exists():
            msg = "Pages did not create PDF"
            raise RuntimeError(msg)

        if output_path.stat().st_size == 0:
            msg = "Generated PDF is empty"
            raise RuntimeError(msg)

    @classmethod
    def render_invoice_pdf_fallback(cls, output_path: Path, data: dict[str, str]) -> None:
        LOGGER.info("Rendering fallback invoice PDF: %s", output_path)
        pdf = canvas.Canvas(str(output_path), pagesize=A4)

        _, height = A4

        pdf.setTitle(f"Invoice {data['invoice_number']}")

        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawString(40, height - cls.FALLBACK_TITLE_Y, "INVOICE")

        pdf.setFont("Helvetica", 12)

        lines = [
            f"Invoice number: {data['invoice_number']}",
            f"Date: {data['date']}",
            f"Period: {data['period_from']} - {data['period_to']}",
            f"Amount: EUR {data['amount']}",
        ]

        y_position = height - cls.FALLBACK_BODY_START_Y

        for line in lines:
            pdf.drawString(40, y_position, line)
            y_position -= cls.FALLBACK_LINE_STEP

        pdf.setFont("Helvetica", 10)

        pdf.drawString(
            40,
            y_position - 20,
            "Generated automatically from invoice template.",
        )
        pdf.save()

    @classmethod
    def render_invoice_pdf(cls, rendered_docx_path: Path, output_path: Path, data: dict[str, str]) -> None:
        try:
            cls.render_invoice_pdf_with_pages(
                rendered_docx_path=rendered_docx_path,
                output_path=output_path,
            )
        except Exception as error:
            e = error
            LOGGER.warning(
                "Pages export failed, using fallback PDF renderer: %s",
                e,
            )
            cls.render_invoice_pdf_fallback(
                output_path=output_path,
                data=data,
            )

    @classmethod
    def build_pages_export_script(cls, rendered_docx_path: Path, output_path: Path) -> list[str]:
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

    @classmethod
    def build_osascript_command(cls, script_lines: list[str]) -> list[str]:
        command = ["osascript"]

        for line in script_lines:
            command.extend(["-e", line])

        return command
