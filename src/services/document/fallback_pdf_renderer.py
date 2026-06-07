"""Базовый рендерер простых fallback-PDF без DOCX-шаблонов."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class FallbackPdfRenderer:
    """Рисует простой PDF из заголовка и набора строк."""

    TITLE_Y = 60
    BODY_START_Y = 120
    LINE_STEP = 24

    @classmethod
    def render_lines(
        cls,
        output_path: Path,
        title: str,
        lines: list[str],
        pdf_title: str,
    ) -> None:
        """Создаёт PDF-документ из заранее подготовленных строк."""

        pdf = canvas.Canvas(str(output_path), pagesize=A4)
        _, height = A4

        pdf.setTitle(pdf_title)

        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawString(40, height - cls.TITLE_Y, title)

        pdf.setFont("Helvetica", 12)
        y_position = height - cls.BODY_START_Y

        for line in lines:
            pdf.drawString(40, y_position, line)
            y_position -= cls.LINE_STEP

        pdf.save()
