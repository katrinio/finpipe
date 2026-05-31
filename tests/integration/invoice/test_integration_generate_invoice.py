from zipfile import ZipFile

from pypdf import PdfReader

from src.constants import TestData
from src.services.invoice.invoice_generator import generate_invoice
from src.services.invoice.invoice_models import InvoiceData


def read_docx_xml_text(docx_path):
    with ZipFile(docx_path) as docx:
        return "\n".join(docx.read(name).decode("utf-8", errors="ignore") for name in docx.namelist() if name.endswith(".xml"))


def test_generate_invoice_creates_pdf(tmp_path):
    output_pdf = tmp_path / "test_invoice.pdf"

    invoice_data = {
        "account_holder": "John Doe",
        "account_holder_address": "Amsterdam",
        "account_bic": "ABNANL2A",
        "account_iban": "NL91ABNA0417164300",
        "account_number": "123456789",
        "amount": "1000",
        "bank_name": "ABN AMRO",
        "company_address": "Belgrade",
        "company_name": "Acme Ltd",
        "date_from": "01.05.2020",
        "date_to": "31.05.2020",
        "invoice_date": "31.05.2020",
        "invoice_number": "2026-05",
        "service_agreement_date": "31.05.1994",
    }

    data = InvoiceData(**invoice_data)

    generate_invoice(
        template_path=TestData.INVOICE_TEMPLATE_PATH,
        output_pdf_path=output_pdf,
        data=data,
    )

    generated_docx = output_pdf.with_suffix(".docx")

    assert generated_docx.exists()
    assert output_pdf.exists()
    assert generated_docx.stat().st_size > 0
    assert output_pdf.stat().st_size > 0

    docx_xml_text = read_docx_xml_text(generated_docx)
    assert "{{" not in docx_xml_text
    assert "}}" not in docx_xml_text

    reader = PdfReader(output_pdf)

    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    for key, value in invoice_data.items():
        assert value in text, f"{key}: {value} не обнаружен в итоговом pdf."
