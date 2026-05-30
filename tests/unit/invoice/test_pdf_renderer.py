from src.services.invoice.invoice_pdf_renderer import InvoiceFallbackPdfRenderer


def test_invoice_fallback_lines_include_all_invoice_fields() -> None:
    data = {
        "account_holder": "Katrin",
        "account_holder_address": "Belgrade",
        "company_name": "Client Ltd",
        "company_address": "Hong Kong",
        "invoice_number": "2026-05",
        "invoice_date": "30.05.2026",
        "date_from": "01.05.2026",
        "date_to": "31.05.2026",
        "service_agreement_date": "01.05.2025",
        "amount": "1000",
        "bank_name": "ALTA BANKA",
        "account_number": "190-128270-73",
        "account_bic": "JMBNRSBG",
        "account_iban": "RS35190007100004318945",
    }

    assert InvoiceFallbackPdfRenderer.build_lines(data) == [
        "From: Katrin",
        "From address: Belgrade",
        "To: Client Ltd",
        "To address: Hong Kong",
        "Invoice number: 2026-05",
        "Invoice date: 30.05.2026",
        "Period: 01.05.2026 - 31.05.2026",
        "Service agreement date: 01.05.2025",
        "Amount: EUR 1000",
        "Bank name: ALTA BANKA",
        "Account number: 190-128270-73",
        "SWIFT/BIC: JMBNRSBG",
        "IBAN: RS35190007100004318945",
    ]
