from dataclasses import dataclass


@dataclass
class TransferData:
    account_number: str
    invoice_date: str
    amount_eur: str
    client_name: str
