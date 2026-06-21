from src.constants import TestData
from src.services.bank.bank_extract import extract_amount


def test_extract_amount_reads_correct_value_from_bank_pdf(tmp_path):
    amount = extract_amount(TestData.BANK_TEMPLATE_PATH)

    assert amount == 1234.56
