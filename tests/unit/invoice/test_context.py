from datetime import date

from src.services.invoice.invoice_context import InvoicePeriod, build_invoice_period


def test_build_invoice_period_for_may_2026() -> None:
    invoice_period = build_invoice_period(
        today=date(2026, 5, 15),
    )

    assert invoice_period.invoice_number == "2026-05"
    assert invoice_period.invoice_date == "15.05.2026"
    assert invoice_period.period_from == "01.05.2026"
    assert invoice_period.period_to == "31.05.2026"


def test_build_invoice_period_for_february_2024() -> None:
    invoice_period = build_invoice_period(
        today=date(2024, 2, 10),
    )

    assert invoice_period.invoice_number == "2024-02"
    assert invoice_period.invoice_date == "10.02.2024"
    assert invoice_period.period_from == "01.02.2024"
    assert invoice_period.period_to == "29.02.2024"


def test_invoice_period_as_template_data() -> None:
    invoice_period = InvoicePeriod(
        invoice_number="2026-05",
        invoice_date="15.05.2026",
        period_from="01.05.2026",
        period_to="31.05.2026",
    )

    assert invoice_period.as_template_data() == {
        "invoice_number": "2026-05",
        "date": "15.05.2026",
        "period_from": "01.05.2026",
        "period_to": "31.05.2026",
    }
