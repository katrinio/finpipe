import pytest
from pypdf import PdfReader

from src.constants import TestData
from src.infrastructure.document import DocxToPdfConverter


@pytest.mark.skipif(
    not DocxToPdfConverter.has_available_converter(),
    reason="Pages.app on macOS or LibreOffice is required for DOCX to PDF conversion integration test.",
)
def test_docx_to_pdf_converter_exports_docx(tmp_path):
    rendered_docx_path = tmp_path / "conversion_order.docx"
    output_pdf_path = tmp_path / "conversion_order.pdf"
    rendered_docx_path.write_bytes(TestData.CONVERSION_ORDER_TEMPLATE_PATH.read_bytes())

    DocxToPdfConverter.convert(
        rendered_docx_path=rendered_docx_path,
        output_path=output_pdf_path,
    )

    assert output_pdf_path.exists()
    assert output_pdf_path.stat().st_size > 0

    reader = PdfReader(output_pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "ALTA BANKA" in text
    assert "deviznog računa" in text
