"""Модели данных для шаблона Conversion Order."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConversionOrderData:
    """Поля, которые подставляются в Conversion Order."""

    account_number: str
    exchange_amount_eur: str
    city: str
    date: str
    name: str
