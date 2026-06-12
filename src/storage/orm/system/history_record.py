"""ORM-сущность истории генерации Invoice."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Integer, String, Text, select, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class InvoiceGenerationStatus(StrEnum):
    """Статус попытки генерации Invoice."""

    SUCCESS = "success"
    FAILED = "failed"


class HistoryRecord(BaseModel):
    """Хранит историю попыток генерации Invoice."""

    __tablename__ = "invoice_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String, index=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=InvoiceGenerationStatus.SUCCESS,
        server_default=text(f"'{InvoiceGenerationStatus.SUCCESS.value}'"),
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    @classmethod
    def add_attempt(
        cls,
        invoice_number: str,
        telegram_id: int | None,
        status: InvoiceGenerationStatus,
        error_message: str | None = None,
    ) -> None:
        """Сохраняет результат отдельной попытки генерации Invoice."""

        with cls.session() as session:
            session.add(
                cls(
                    invoice_number=invoice_number,
                    telegram_id=telegram_id,
                    status=status,
                    error_message=error_message,
                )
            )
            session.commit()

    @classmethod
    def list_by_invoice_number(cls, invoice_number: str) -> list["HistoryRecord"]:
        """Возвращает все попытки генерации для номера Invoice."""

        with cls.session() as session:
            statement = select(cls).where(cls.invoice_number == invoice_number).order_by(cls.created_at.asc(), cls.id.asc())
            return list(session.scalars(statement))

    @classmethod
    def get_last_attempt(cls, invoice_number: str) -> "HistoryRecord | None":
        """Возвращает последнюю попытку генерации для номера Invoice."""

        with cls.session() as session:
            statement = select(cls).where(cls.invoice_number == invoice_number).order_by(cls.created_at.desc(), cls.id.desc()).limit(1)
            return session.scalar(statement)

    @classmethod
    def has_attempts(cls, invoice_number: str) -> bool:
        """Проверяет, есть ли история генераций для номера Invoice."""

        return cls.get_last_attempt(invoice_number) is not None
