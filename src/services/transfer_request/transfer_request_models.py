from dataclasses import dataclass


@dataclass(frozen=True)
class TransferRequestData:
    account_number: str
    amount: str
    city: str
    date: str
    name: str
