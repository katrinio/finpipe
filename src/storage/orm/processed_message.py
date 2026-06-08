"""ORM-сущность обработанного письма банка."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class ProcessedMessage(BaseModel):
    """Письмо банка, уже отмеченное как обработанное."""

    __tablename__ = "processed_messages"
    __pk_column_name__ = "message_id"

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )
