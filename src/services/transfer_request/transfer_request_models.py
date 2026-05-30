from dataclasses import dataclass


@dataclass(frozen=True)
class TransferRequestTemplateDetails:
    placeholder_aliases: dict[str, tuple[str, ...]]


TRANSFER_REQUEST_TEMPLATE_DETAILS = TransferRequestTemplateDetails(
    placeholder_aliases={
        "account_number": ("accountNumber",),
        "amount": ("amount",),
        "city": ("city",),
        "date": ("date",),
        "name": ("name",),
    },
)


@dataclass
class TransferData:
    account_number: str
    invoice_date: str
    amount_eur: str
    client_name: str
