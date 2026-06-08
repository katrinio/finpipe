"""ORM-сущность записи истории инвойсов."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseStorage


class UserConfig(BaseStorage):
    """Запись о пользователях."""

    __tablename__ = "user_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer)
    user_name: Mapped[str] = mapped_column(String)
    account_holder: Mapped[str] = mapped_column(String)
    account_holder_email: Mapped[str] = mapped_column(String)
    account_holder_address: Mapped[str] = mapped_column(String)
    bank_name: Mapped[str] = mapped_column(String)
    account_number: Mapped[str] = mapped_column(String)
    iban: Mapped[str] = mapped_column(String)
    bic: Mapped[str] = mapped_column(String)
    company_name: Mapped[str] = mapped_column(String)
    company_address: Mapped[str] = mapped_column(String)
    service_agreement_date: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
