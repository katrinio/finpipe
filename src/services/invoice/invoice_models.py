from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceTemplateDetails:
    placeholder_aliases: dict[str, tuple[str, ...]]


INVOICE_TEMPLATE_DETAILS = InvoiceTemplateDetails(
    placeholder_aliases={
        "account_holder": ("accountHolder",),
        "account_holder_address": ("accountHolderAddress",),
        "company_name": ("companyName",),
        "company_address": ("companyAddress",),
        "invoice_number": ("invoiceId",),
        "date": ("invoiceDate",),
        "period_from": ("dateFrom",),
        "period_to": ("dateTo",),
        "service_agreement_date": ("serviceAgreementDate",),
        "amount": ("amount",),
        "bank_name": ("bankName",),
        "account_number": ("accountNumber",),
        "account_bic": ("accountBic",),
        "account_iban": ("accountIban",),
    },
)


@dataclass
class InvoiceData:
    invoice_number: str
    invoice_date: str
    amount_eur: str
    client_name: str
