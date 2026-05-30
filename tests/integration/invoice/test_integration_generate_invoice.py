from pypdf import PdfReader

from src.constants import TestData
from src.services.invoice.invoice_generator import generate_invoice
from src.services.invoice.invoice_models import InvoiceData


def test_generate_invoice_creates_pdf(tmp_path):
    output_pdf = tmp_path / "test_invoice.pdf"

    data = InvoiceData(
        account_holder="John Doe",
        account_holder_address="Amsterdam",
        account_bic="ABNANL2A",
        account_iban="NL91ABNA0417164300",
        account_number="123456789",
        amount="1000",
        bank_name="ABN AMRO",
        company_address="Belgrade",
        company_name="Acme Ltd",
        date_from="01.05.2020",
        date_to="31.05.2020",
        invoice_date="31.05.2020",
        invoice_number="2026-05",
        service_agreement_date="31.05.1994",
    )

    generate_invoice(
        template_path=TestData.TEMPLATE_PATH,
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

    assert "John Doe" in text
    assert "1000" in text
    assert "2026-05" in text
