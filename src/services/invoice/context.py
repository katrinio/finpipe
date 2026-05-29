from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from src.utils import Utils


@dataclass(frozen=True)
class InvoicePeriod:
    invoice_number: str
    invoice_date: str
    period_from: str
    period_to: str

    def as_template_data(self) -> dict[str, str]:
        return {
            "invoice_number": self.invoice_number,
            "date": self.invoice_date,
            "period_from": self.period_from,
            "period_to": self.period_to,
        }


def build_invoice_period(today: date | None = None) -> InvoicePeriod:
    current_day = today or Utils.today()

    period_from = current_day.replace(day=1)

    period_to = current_day.replace(
        day=monthrange(
            current_day.year,
            current_day.month,
        )[1]
    )

    return InvoicePeriod(
        invoice_number=build_invoice_number(current_day),
        invoice_date=current_day.strftime("%d.%m.%Y"),
        period_from=period_from.strftime("%d.%m.%Y"),
        period_to=period_to.strftime("%d.%m.%Y"),
    )


def build_invoice_number(current_day: date) -> str:
    return current_day.strftime("%Y-%m")
