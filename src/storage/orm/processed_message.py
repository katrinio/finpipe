"""ORM-сущность обработанного письма банка."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.exc import IntegrityError
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

    @classmethod
    def list_message_ids(cls) -> list[str]:
        with cls.session() as session:
            return cls.list_primary_keys(session)

    @classmethod
    def is_processed(cls, message_id: str) -> bool:
        with cls.session() as session:
            return cls.exists_by_primary_key(session, message_id)

    @classmethod
    def mark_as_processed(cls, message_id: str) -> None:
        with cls.session() as session:
            cls.add_by_primary_key(session, message_id)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    @classmethod
    def replace_all(cls, message_ids: set[str]) -> None:
        """Полностью заменяет содержимое таблицы обработанных писем."""

        with cls.session() as session:
            cls.replace_primary_keys(session, sorted(message_ids))
            session.commit()

    @classmethod
    def clear_processed_message(cls) -> None:
        with cls.session() as session:
            cls.clear(session)
            session.commit()
