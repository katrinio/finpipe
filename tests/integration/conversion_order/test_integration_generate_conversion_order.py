from pypdf import PdfReader

from src.constants import TestData
from src.services.conversion_order.generate import generate_conversion_order
from src.services.conversion_order.models import ConversionOrderData


def test_generate_conversion_order_creates_pdf(tmp_path):
    output_pdf = tmp_path / "test_conversion_order.pdf"

    conversion_order_data = {"account_number": "123456789", "amount": "1000", "city": "Belgrade", "date": "01.05.2020", "name": "Bela Lugoshi"}

    data = ConversionOrderData(**conversion_order_data)

    generate_conversion_order(
        template_path=TestData.CONVERSION_ORDER_TEMPLATE_PATH,
        output_pdf_path=output_pdf,
        data=data,
    )

    generated_docx = output_pdf.with_suffix(".docx")

    assert generated_docx.exists()
    assert output_pdf.exists()
    assert generated_docx.stat().st_size > 0
    assert output_pdf.stat().st_size > 0

    reader = PdfReader(output_pdf)

    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    for key, value in conversion_order_data.items():
        assert value in text, f"{key}: {value} не обнаружен в итоговом pdf."
