"""ORM-сущность разрешённого Telegram-пользователя."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, String, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class UserRole(StrEnum):
    OWNER = "owner"
    USER = "user"
    ADMIN = "admin"


class AllowedUser(BaseModel):
    """Пользователь, которому разрешён доступ в Telegram-бот."""

    __tablename__ = "allowed_users"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    def __init__(
        self,
        telegram_id: int,
        username: str | None = None,
        user_name: str | None = None,
        role: str | None = None,
    ) -> None:
        self.telegram_id = telegram_id
        self.username = username if username is not None else user_name
        self.role = role or UserRole.USER

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
    def get_owner(cls) -> "AllowedUser | None":
        with cls.session() as session:
            statement = select(cls).where(cls.role == UserRole.OWNER).order_by(cls.telegram_id.asc()).limit(1)
            return session.scalar(statement)

    @classmethod
    def is_owner(cls, telegram_id: int) -> bool:
        user = cls.get_by_telegram_id(telegram_id)
        return user is not None and user.role == UserRole.OWNER

    @classmethod
    def is_admin(cls, telegram_id: int) -> bool:
        user = cls.get_by_telegram_id(telegram_id)
        return user is not None and user.role in {UserRole.OWNER, UserRole.ADMIN}

    @classmethod
    def create(cls, telegram_id: int, username: str | None = None, role: str | None = None) -> None:
        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            entity = session.scalar(statement)
            if entity is None:
                session.add(cls(telegram_id=telegram_id, username=username, role=role or UserRole.USER))
            elif username is not None:
                entity.username = username
                if role is not None:
                    entity.role = role
            session.commit()

    @classmethod
    def upsert(cls, telegram_id: int, username: str | None = None, role: str | None = None) -> None:
        cls.create(telegram_id=telegram_id, username=username, role=role)

    @classmethod
    def add(cls, telegram_id: int, user_name: str) -> None:
        cls.create(telegram_id=telegram_id, username=user_name)

    @classmethod
    def list_all(cls) -> list["AllowedUser"]:
        with cls.session() as session:
            statement = select(cls).order_by(cls.telegram_id)
            return list(session.scalars(statement))

    @classmethod
    def delete(cls, telegram_id: int) -> None:
        """Удаляет пользователя из allowlist."""

        with cls.session() as session:
            session.execute(delete(cls).where(cls.telegram_id == telegram_id))
            session.commit()

    @property
    def user_name(self) -> str | None:
        return self.username

    @user_name.setter
    def user_name(self, value: str | None) -> None:
        self.username = value

    @classmethod
    def count(cls) -> int:
        with cls.session() as session:
            statement = select(func.count()).select_from(cls)
            return session.scalar(statement) or 0
