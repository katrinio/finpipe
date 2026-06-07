"""Расчёт периода для transfer request в тех же правилах, что и для invoice."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from src.utils import Utils


@dataclass(frozen=True)
class InvoicePeriod:
    """Период и номер документа для transfer request."""

    invoice_number: str
    invoice_date: str
    period_from: str
    period_to: str


def build_invoice_period(today: date | None = None) -> InvoicePeriod:
    """Строит период transfer request для указанной даты."""

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
    """Формирует номер документа в формате `YYYY-MM`."""

    return current_day.strftime("%Y-%m")
