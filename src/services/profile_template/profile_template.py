from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileTemplate:
    company_name: str | None
    company_address: str | None
    account_holder: str | None
    account_holder_email: str | None
    account_holder_address: str | None
    bank_name: str | None
    registration_number: str | None
    city: str | None
    account_number: str | None
    iban: str | None
    bic: str | None
    service_agreement_date: str | None
    payment_number: str | None
    payment_code: str | None
    payment_description: str | None
