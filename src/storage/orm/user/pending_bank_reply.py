"""Состояние ожидающего отправки ответа банку."""

from datetime import datetime

from sqlalchemy import String, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, DateTime

from src.storage.orm.base import BaseModel


class PendingBankReply(BaseModel):
    """Хранит данные для отложенного ответа на письмо банка."""

    __tablename__ = "pending_bank_reply"

    telegram_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    thread_id: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    cc: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    invoice_pdf_path: Mapped[str] = mapped_column(String, nullable=False)
    bank_confirmation_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())

    @classmethod
    def save(
        cls,
        telegram_id: int,
        thread_id: str,
        subject: str,
        sender: str,
        cc: str,
        message_id: str,
        invoice_pdf_path: str,
        bank_confirmation_path: str,
    ) -> None:
        with cls.session() as session:
            existing = session.scalar(select(cls).where(cls.telegram_id == telegram_id).limit(1))
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(
                cls(
                    telegram_id=telegram_id,
                    thread_id=thread_id,
                    subject=subject,
                    sender=sender,
                    cc=cc,
                    message_id=message_id,
                    invoice_pdf_path=invoice_pdf_path,
                    bank_confirmation_path=bank_confirmation_path,
                )
            )
            session.commit()

    @classmethod
    def get(cls, telegram_id: int) -> "PendingBankReply | None":
        with cls.session() as session:
            return session.scalar(select(cls).where(cls.telegram_id == telegram_id).limit(1))

    @classmethod
    def clear(cls, telegram_id: int) -> None:
        with cls.session() as session:
            session.query(cls).where(cls.telegram_id == telegram_id).delete()
            session.commit()
