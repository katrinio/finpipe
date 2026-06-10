"""ORM-сущность пользовательских настроек."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, delete, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class CompanyProfile(BaseModel):
    """CompanyProfile."""

    __tablename__ = "company_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    owner_telegram_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String)
    company_address: Mapped[str] = mapped_column(String)
    service_agreement_date: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> CompanyProfile | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def exists(cls, owner_telegram_id: int) -> bool:
        """Проверяет наличие записи владельца."""

        return cls.get_by_owner(owner_telegram_id) is not None

    @classmethod
    def delete(cls, owner_telegram_id: int) -> None:
        """Удаляет запись владельца."""

        with cls.session() as session:
            statement = delete(cls).where(cls.owner_telegram_id == owner_telegram_id)
            session.execute(statement)
            session.commit()

    @classmethod
    def update(cls, owner_telegram_id: int, **fields: object) -> None:
        """Обновляет поля записи владельца."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == owner_telegram_id).limit(1)
            entity = session.scalar(statement)

            if entity is None:
                raise ValueError(f"{cls.__name__} for owner {owner_telegram_id} not found")

            for field_name, value in fields.items():
                setattr(entity, field_name, value)

            session.commit()
