from src.services.conversion_order.render_pdf import ConversionOrderFallbackPdfRenderer


def test_conversion_order_fallback_lines_include_all_fields() -> None:
    data = {
        "account_number": "190-128270-73",
        "exchange_amount_eur": "1000.00",
        "city": "Beograd",
        "date": "30.05.2026",
        "name": "Katrin",
    }

    assert ConversionOrderFallbackPdfRenderer.build_lines(data) == [
        "Account number: 190-128270-73",
        "Date: 30.05.2026",
        "City: Beograd",
        "Name: Katrin",
        "Amount: EUR 1000.00",
    ]
