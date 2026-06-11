"""ORM-сущность разрешённого Telegram-пользователя."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, String, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class AuditStatus(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILED = "FAILED"


class AuditLog(BaseModel):
    """Пользователь, которому разрешён доступ в Telegram-бот."""

    __tablename__ = "audit_log"
    __pk_column_name__ = "id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[str] = mapped_column(String, nullable=True)

    @classmethod
    def create(
        cls,
        telegram_id: int,
        user_name: str,
        command: str,
        status: str,
        details: str | None = None,
    ) -> None:
        with cls.session() as session:
            session.add(
                cls(
                    telegram_id=telegram_id,
                    user_name=user_name,
                    command=command,
                    status=status,
                    details=details,
                )
            )
            session.commit()

    @classmethod
    def list_recent(cls, limit: int = 50) -> list["AuditLog"]:
        with cls.session() as session:
            statement = select(cls).order_by(cls.created_at.desc()).limit(limit)
            return list(session.scalars(statement))

    @classmethod
    def clear(cls) -> None:
        with cls.session() as session:
            session.execute(delete(cls))
            session.commit()
