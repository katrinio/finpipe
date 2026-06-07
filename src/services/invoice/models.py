"""Модели данных для подстановки в инвойс."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceData:
    """Полный набор полей, который нужен шаблону инвойса."""

    account_holder: str
    account_holder_address: str
    account_bic: str
    account_iban: str
    account_number: str
    amount: str
    bank_name: str
    company_address: str
    company_name: str
    date_from: str
    date_to: str
    invoice_date: str
    invoice_number: str
    service_agreement_date: str
