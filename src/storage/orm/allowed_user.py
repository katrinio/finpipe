"""ORM-сущность разрешённого Telegram-пользователя."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class AllowedUser(BaseModel):
    """Пользователь, которому разрешён доступ в Telegram-бот."""

    __tablename__ = "allowed_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> "AllowedUser | None":
        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def list_all(cls) -> list["AllowedUser"]:
        with cls.session() as session:
            statement = select(cls).order_by(cls.telegram_id)
            return list(session.scalars(statement))

    @classmethod
    def add(cls, telegram_id: int, user_name: str) -> None:
        with cls.session() as session:
            if cls.get_by_telegram_id(telegram_id):
                return
            session.add(cls(telegram_id=telegram_id, user_name=user_name))
