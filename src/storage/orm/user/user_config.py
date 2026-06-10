"""ORM-сущность пользовательских настроек."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Boolean, DateTime

from src.storage.orm.base import BaseModel


class UserConfig(BaseModel):
    """Пользовательские настройки, включая Telegram-привязку."""

    __tablename__ = "user_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> UserConfig | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def create(cls, telegram_id: int, user_name: str) -> None:
        """Создаёт пользователя или обновляет username."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            user = session.execute(statement).scalar_one_or_none()

            if user is None:
                user = UserConfig(telegram_id=telegram_id, user_name=user_name)
                session.add(user)
            else:
                user.user_name = user_name

            session.commit()
