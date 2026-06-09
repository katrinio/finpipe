from src.constants import TestData
from src.services.bank.bank_extract import extract_amount


def test_generate_invoice_creates_pdf(tmp_path):
    amount = extract_amount(TestData.BANK_TEMPLATE_PATH)

    assert amount == 1234.56
