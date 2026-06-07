"""ORM-сущность обработанных Telegram update_id."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseStorage


class TelegramUpdate(BaseStorage):
    """Обработанный Telegram update_id."""

    __tablename__ = "telegram_updates"

    update_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )
