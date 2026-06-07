"""Модели данных для работы с Gmail."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BankEmail:
    """Краткое представление письма банка, нужное workflow."""

    subject: str
    sender: str
    date: str
    message_id: str
    thread_id: str
