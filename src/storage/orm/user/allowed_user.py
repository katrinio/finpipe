"""ORM-сущность разрешённого Telegram-пользователя."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class AllowedUser(BaseModel):
    """Пользователь, которому разрешён доступ в Telegram-бот."""

    __tablename__ = "allowed_users"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    def __init__(
        self,
        telegram_id: int,
        username: str | None = None,
        user_name: str | None = None,
    ) -> None:
        self.telegram_id = telegram_id
        self.username = username if username is not None else user_name

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> "AllowedUser | None":
        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def exists(cls, telegram_id: int) -> bool:
        with cls.session() as session:
            statement = select(cls.telegram_id).where(cls.telegram_id == telegram_id).limit(1)
            return session.scalar(statement) is not None

    @classmethod
    def create(cls, telegram_id: int, username: str | None = None) -> None:
        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            entity = session.scalar(statement)
            if entity is None:
                session.add(cls(telegram_id=telegram_id, username=username))
            elif username is not None:
                entity.username = username
            session.commit()

    @classmethod
    def upsert(cls, telegram_id: int, username: str | None = None) -> None:
        cls.create(telegram_id=telegram_id, username=username)

    @classmethod
    def add(cls, telegram_id: int, user_name: str) -> None:
        cls.create(telegram_id=telegram_id, username=user_name)

    @classmethod
    def list_all(cls) -> list["AllowedUser"]:
        with cls.session() as session:
            statement = select(cls).order_by(cls.telegram_id)
            return list(session.scalars(statement))

    @property
    def user_name(self) -> str | None:
        return self.username

    @user_name.setter
    def user_name(self, value: str | None) -> None:
        self.username = value
