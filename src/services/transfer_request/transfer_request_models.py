"""Модели данных для шаблона transfer request."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferRequestData:
    """Поля, которые подставляются в transfer request."""

    account_number: str
    amount: str
    city: str
    date: str
    name: str
