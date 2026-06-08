"""ORM-сущность разрешённого Telegram-пользователя."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseStorage


class AuditStatus(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILED = "FAILED"


class AuditLog(BaseStorage):
    """Пользователь, которому разрешён доступ в Telegram-бот."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[str] = mapped_column(String, nullable=True)
