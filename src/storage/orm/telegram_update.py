"""ORM-сущность обработанных Telegram update_id."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class TelegramUpdate(BaseModel):
    """Обработанный Telegram update_id."""

    __tablename__ = "telegram_updates"
    __pk_column_name__ = "update_id"

    update_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    @classmethod
    def is_processed(cls, update_id: int) -> bool:
        with cls.session() as session:
            return TelegramUpdate.exists_by_primary_key(session, update_id)

    @classmethod
    def get_last_processed_update_id(cls) -> int | None:
        with cls.session() as session:
            return TelegramUpdate.get_last_primary_key(session)

    @classmethod
    def mark_processed(cls, update_id: int) -> None:
        with cls.session() as session:
            TelegramUpdate.add_by_primary_key(session, update_id)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
