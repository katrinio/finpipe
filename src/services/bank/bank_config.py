"""Known bank configurations — addresses and identifiers specific to each bank."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BankConfig:
    name: str
    confirmation_email_sender: str
    reply_cc: str
    conversion_to: str
    conversion_cc: str


KNOWN_BANKS: dict[str, BankConfig] = {
    "altabanka": BankConfig(
        name="Alta Banka",
        confirmation_email_sender="devizniprilivi.obavestenja@altabanka.rs",
        reply_cc="devprilivi@altabanka.rs",
        conversion_to="otkup@altabanka.rs",
        conversion_cc="treasury@altabanka.rs",
    ),
}


def get_bank_config(bank_slug: str | None) -> BankConfig | None:
    if not bank_slug:
        return None
    return KNOWN_BANKS.get(bank_slug.lower().strip())
