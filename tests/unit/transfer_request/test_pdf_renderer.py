from src.services.transfer_request.transfer_request_pdf_renderer import TransferRequestFallbackPdfRenderer


def test_transfer_request_fallback_lines_include_all_transfer_request_fields() -> None:
    data = {
        "account_number": "190-128270-73",
        "amount": "1000",
        "city": "Beograd",
        "date": "30.05.2026",
        "name": "Katrin",
    }

    assert TransferRequestFallbackPdfRenderer.build_lines(data) == [
        "Account number: 190-128270-73",
        "Date: 30.05.2026",
        "City: Beograd",
        "Name: Katrin",
        "Amount: EUR 1000",
    ]
