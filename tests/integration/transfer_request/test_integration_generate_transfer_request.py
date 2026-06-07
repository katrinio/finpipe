from pypdf import PdfReader

from src.constants import TestData
from src.services.transfer_request.generate import generate_transfer_request
from src.services.transfer_request.models import TransferRequestData


def test_generate_transfer_request_creates_pdf(tmp_path):
    output_pdf = tmp_path / "test_transfer_request.pdf"

    transfer_request_data = {"account_number": "123456789", "amount": "1000", "city": "Belgrade", "date": "01.05.2020", "name": "Bela Lugoshi"}

    data = TransferRequestData(**transfer_request_data)

    generate_transfer_request(
        template_path=TestData.TRANSFER_TEMPLATE_PATH,
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

    for key, value in transfer_request_data.items():
        assert value in text, f"{key}: {value} не обнаружен в итоговом pdf."
