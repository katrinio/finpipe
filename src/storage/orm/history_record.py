"""ORM-сущность записи истории инвойсов."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseTable


class HistoryRecord(BaseTable):
    """Запись об уже созданном инвойсе."""

    __tablename__ = "invoice_history"
    __pk_column_name__ = "invoice_number"

    invoice_number: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )
