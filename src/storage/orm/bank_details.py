from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Float

from src.storage.orm.base import BaseModel


class BankAccount(BaseModel):
    """BankAccount."""

    __tablename__ = "bank_account"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    owner_telegram_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    account_holder: Mapped[str] = mapped_column(String)
    account_holder_email: Mapped[str] = mapped_column(String)
    account_holder_address: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    bank_name: Mapped[str] = mapped_column(String)
    account_number: Mapped[str] = mapped_column(String)
    iban: Mapped[str] = mapped_column(String)
    bic: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> BankAccount | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == telegram_id).limit(1)
            return session.scalar(statement)
