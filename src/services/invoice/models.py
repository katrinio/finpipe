from dataclasses import dataclass


@dataclass
class InvoiceData:
    invoice_number: str
    invoice_date: str
    amount_eur: str
    client_name: str
