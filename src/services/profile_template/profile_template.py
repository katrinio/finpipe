from dataclasses import dataclass


@dataclass(frozen=True)
class BankConfirmationEmailTemplate:
    """Параметры поиска письма банка в профиле."""

    recipient: str | None
    subject_contains: str | None


@dataclass(frozen=True)
class ProfileTemplate:
    """Нормализованные поля профиля из YAML-шаблона."""

    company_name: str | None
    company_address: str | None
    company_email: str | None
    account_holder: str | None
    account_holder_email: str | None
    account_holder_address: str | None
    bank_name: str | None
    bank_slug: str | None
    registration_number: str | None
    city: str | None
    account_number: str | None
    iban: str | None
    bic: str | None
    service_agreement_date: str | None
    payment_number: str | None
    payment_code: str | None
    payment_description: str | None
    bank_confirmation_email: BankConfirmationEmailTemplate
