from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from src.infrastructure.document import PdfGetPageSize
from src.services.signing.context import PdfSignaturePosition
from src.utils.credentials import LOGGER


class PdfSigner:
    @classmethod
    def sign(cls, input_pdf: Path, signature: Path, position: PdfSignaturePosition) -> None:
        reader = PdfReader(str(input_pdf))
        page = reader.pages[0]

        packet = BytesIO()
        overlay = canvas.Canvas(packet, pagesize=PdfGetPageSize.get_page_size(page))

        cls.draw_signature(
            pdf_canvas=overlay,
            signature=signature,
            position=position,
        )

        overlay.save()
        packet.seek(0)

        # TODO: merge overlay with source PDF
        # TODO: save result to output_pdf

    @classmethod
    def draw_signature(cls, pdf_canvas: canvas.Canvas, signature: Path, position: PdfSignaturePosition) -> None:
        if not signature.exists():
            LOGGER.warning("Signature image does not exist: %s", signature)
            return

        width, height = cls._get_signature_size(
            signature,
            position.height,
        )

        pdf_canvas.drawImage(
            str(signature),
            position.x,
            position.y,
            width=width,
            height=height,
            mask="auto",
        )

    @classmethod
    def _get_signature_size(cls, signature: Path, target_height: int) -> tuple[int, int]:
        """Вычисляет ширину подписи с сохранением пропорций."""

        with Image.open(signature) as image:
            original_width, original_height = image.size

        scale = target_height / original_height
        return (
            round(original_width * scale),
            target_height,
        )
