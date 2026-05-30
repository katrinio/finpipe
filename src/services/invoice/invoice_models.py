from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceData:
    invoice_number: str
    date: str
    period_from: str
    period_to: str
    amount: str
