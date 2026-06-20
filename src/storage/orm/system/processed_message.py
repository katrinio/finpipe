"""ORM-сущность обработанного письма банка."""

from datetime import datetime

from sqlalchemy import String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class ProcessedMessage(BaseModel):
    """Письмо банка, уже отмеченное как обработанное."""

    __tablename__ = "processed_messages"
    __pk_column_name__ = "message_id"

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())

    @classmethod
    def list_message_ids(cls) -> list[str]:
        with cls.session() as session:
            statement = select(cls.message_id).order_by(cls.message_id)
            return list(session.scalars(statement))

    @classmethod
    def get_by_message_id(cls, message_id: str) -> "ProcessedMessage | None":
        with cls.session() as session:
            statement = select(cls).where(cls.message_id == message_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def is_processed(cls, message_id: str) -> bool:
        with cls.session() as session:
            statement = select(cls.message_id).where(cls.message_id == message_id).limit(1)
            return session.scalar(statement) is not None

    @classmethod
    def exists(cls, message_id: str) -> bool:
        return cls.is_processed(message_id)

    @classmethod
    def mark_as_processed(cls, message_id: str) -> None:
        with cls.session() as session:
            session.add(cls(message_id=message_id))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    @classmethod
    def replace_all(cls, message_ids: set[str]) -> None:
        """Полностью заменяет содержимое таблицы обработанных писем."""

        with cls.session() as session:
            session.query(cls).delete()
            session.add_all(cls(message_id=message_id) for message_id in sorted(message_ids))
            session.commit()

    @classmethod
    def unmark(cls, message_id: str) -> None:
        """Снимает отметку обработанного письма, чтобы оно могло быть обработано снова."""
        with cls.session() as session:
            session.query(cls).filter(cls.message_id == message_id).delete()
            session.commit()

    @classmethod
    def clear_processed_message(cls) -> None:
        with cls.session() as session:
            session.query(cls).delete()
            session.commit()
