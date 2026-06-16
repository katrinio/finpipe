"""ORM-сущность истории генерации документов."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, DateTime

from src.storage.orm.base import BaseModel


class DocumentType(StrEnum):
    """Тип поддерживаемого документа."""

    SALARY_INVOICE = "salary_invoice"
    BANK_CONFIRMATION = "bank_confirmation"
    CONVERSION_ORDER = "conversion_order"


class DocumentGenerationStatus(StrEnum):
    """Статус операции генерации документа."""

    SUCCESS = "success"
    FAILED = "failed"


class DocumentGenerationHistory(BaseModel):
    """Хранит историю операций генерации документов."""

    __tablename__ = "document_generation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_type: Mapped[str] = mapped_column(
        String, nullable=False, default=DocumentType.SALARY_INVOICE, server_default=DocumentType.SALARY_INVOICE.value, index=True
    )
    document_number: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    telegram_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=DocumentGenerationStatus.SUCCESS, server_default=DocumentGenerationStatus.SUCCESS
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    @classmethod
    def add_attempt(
        cls,
        document_type: DocumentType,
        document_number: str | None,
        telegram_id: int | None,
        status: DocumentGenerationStatus,
        error_message: str | None = None,
    ) -> None:
        """Сохраняет результат отдельной попытки генерации документа."""

        with cls.session() as session:
            session.add(
                cls(
                    document_type=document_type,
                    document_number=document_number,
                    telegram_id=telegram_id,
                    status=status,
                    error_message=error_message,
                )
            )
            session.commit()

    @classmethod
    def list_by_document(
        cls,
        document_type: DocumentType,
        document_number: str | None,
    ) -> list["DocumentGenerationHistory"]:
        """Возвращает все попытки генерации для типа и номера документа."""

        with cls.session() as session:
            statement = (
                select(cls)
                .where(cls.document_type == document_type)
                .where(cls.document_number.is_(document_number) if document_number is None else cls.document_number == document_number)
                .order_by(cls.created_at.asc(), cls.id.asc())
            )
            return list(session.scalars(statement))

    @classmethod
    def get_last_attempt(
        cls,
        document_type: DocumentType,
        document_number: str | None,
    ) -> "DocumentGenerationHistory | None":
        """Возвращает последнюю попытку генерации для типа и номера документа."""

        with cls.session() as session:
            statement = (
                select(cls)
                .where(cls.document_type == document_type)
                .where(cls.document_number.is_(document_number) if document_number is None else cls.document_number == document_number)
                .order_by(cls.created_at.desc(), cls.id.desc())
                .limit(1)
            )
            return session.scalar(statement)

    @classmethod
    def has_attempts(cls, document_type: DocumentType, document_number: str | None) -> bool:
        """Проверяет, есть ли история генераций для типа и номера документа."""

        return cls.get_last_attempt(document_type, document_number) is not None

    @classmethod
    def count(cls, document_type: DocumentType) -> int:
        with cls.session() as session:
            statement = select(func.count()).where(cls.document_type == document_type).select_from(cls)
            return session.scalar(statement) or 0
