"""ORM-сущность пользовательских настроек."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class UserConfig(BaseModel):
    """Пользовательские настройки, включая Telegram-привязку."""

    __tablename__ = "user_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
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

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> UserConfig | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def add(cls, telegram_id: int, user_name: str) -> None:
        with cls.session() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            user = session.execute(statement).scalar_one_or_none()

            if user is None:
                user = UserConfig(telegram_id=telegram_id, user_name=user_name)
                session.add(user)
            else:
                user.user_name = user_name

            session.commit()
