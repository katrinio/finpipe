"""DTO сводного статуса пользовательской конфигурации."""

from dataclasses import dataclass


@dataclass(slots=True)
class SystemStatus:
    """Снимок готовности пользовательской конфигурации."""

    company: bool
    bank_details: bool
    signature: bool
    gmail: bool
    bank_email_configured: bool

    bank_confirmation_available: bool
    invoice_available: bool
    conversion_order_available: bool
