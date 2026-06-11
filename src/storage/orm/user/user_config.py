from datetime import datetime

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class UserConfig(BaseModel):
    """Пользовательские настройки."""

    __tablename__ = "user_config"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.current_timestamp())

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> "UserConfig | None":
        """Возвращает настройки пользователя."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)

            return session.scalar(statement)

    @classmethod
    def get_or_create(cls, telegram_id: int) -> "UserConfig":
        """Возвращает настройки пользователя, создавая запись при необходимости."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            config = session.scalar(statement)

            if config is None:
                config = cls(telegram_id=telegram_id)
                session.add(config)
                session.commit()

            return config
