"""ORM-сущность записи истории инвойсов."""

from datetime import datetime

from sqlalchemy import String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class HistoryRecord(BaseModel):
    """Запись об уже созданном инвойсе."""

    __tablename__ = "invoice_history"
    __pk_column_name__ = "invoice_number"

    invoice_number: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    @classmethod
    def list_invoices(cls) -> list[str]:
        with cls.session() as session:
            statement = select(cls.invoice_number).order_by(cls.invoice_number)
            return list(session.scalars(statement))

    @classmethod
    def get_by_invoice_number(cls, invoice_number: str) -> "HistoryRecord | None":
        with cls.session() as session:
            statement = select(cls).where(cls.invoice_number == invoice_number).limit(1)
            return session.scalar(statement)

    @classmethod
    def invoice_exists(cls, invoice_number: str) -> bool:
        with cls.session() as session:
            statement = select(cls.invoice_number).where(cls.invoice_number == invoice_number).limit(1)
            return session.scalar(statement) is not None

    @classmethod
    def exists(cls, invoice_number: str) -> bool:
        return cls.invoice_exists(invoice_number)

    @classmethod
    def add_invoice(cls, invoice_number: str) -> None:
        with cls.session() as session:
            session.add(cls(invoice_number=invoice_number))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    @classmethod
    def get_last_invoice(cls) -> str | None:
        with cls.session() as session:
            statement = select(cls.invoice_number).order_by(cls.invoice_number.desc()).limit(1)
            return session.scalar(statement)
