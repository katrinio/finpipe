"""DTO сводного статуса пользовательской конфигурации."""

from dataclasses import dataclass


@dataclass(slots=True)
class SystemStatus:
    """Снимок готовности пользовательской конфигурации."""

    company: bool
    bank_details: bool
    signature: bool
    invoice_available: bool
