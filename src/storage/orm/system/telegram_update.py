"""ORM-сущность обработанных Telegram update_id."""

from datetime import datetime

from sqlalchemy import Integer, func, select
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
            statement = select(cls.update_id).where(cls.update_id == update_id).limit(1)
            return session.scalar(statement) is not None

    @classmethod
    def get_by_update_id(cls, update_id: int) -> "TelegramUpdate | None":
        with cls.session() as session:
            statement = select(cls).where(cls.update_id == update_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def get_last_processed_update_id(cls) -> int | None:
        with cls.session() as session:
            statement = select(cls.update_id).order_by(cls.update_id.desc()).limit(1)
            return session.scalar(statement)

    @classmethod
    def mark_processed(cls, update_id: int) -> None:
        with cls.session() as session:
            session.add(cls(update_id=update_id))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
