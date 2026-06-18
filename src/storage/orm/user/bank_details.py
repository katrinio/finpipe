"""ORM-модель банковских реквизитов пользователя."""

from datetime import datetime

from sqlalchemy import Integer, String, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, DateTime, Float

from src.storage.orm.base import BaseModel


class BankDetails(BaseModel):
    """Хранит банковские реквизиты, используемые в документах."""

    __tablename__ = "bank_account"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_telegram_id: Mapped[int] = mapped_column(BIGINT, nullable=False, unique=True, index=True)
    account_holder: Mapped[str] = mapped_column(String)
    account_holder_email: Mapped[str | None] = mapped_column(String, nullable=True)
    account_holder_address: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    bank_name: Mapped[str] = mapped_column(String)
    account_number: Mapped[str] = mapped_column(String)
    iban: Mapped[str] = mapped_column(String)
    bic: Mapped[str] = mapped_column(String)
    bank_confirmation_email_sender: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_confirmation_email_recipient: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_confirmation_email_subject_contains: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> BankDetails | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def exists(cls, owner_telegram_id: int) -> bool:
        """Проверяет наличие записи владельца."""

        return cls.get_by_owner(owner_telegram_id) is not None

    @classmethod
    def delete(cls, owner_telegram_id: int) -> None:
        """Удаляет запись владельца."""

        with cls.session() as session:
            statement = delete(cls).where(cls.owner_telegram_id == owner_telegram_id)
            session.execute(statement)
            session.commit()

    @classmethod
    def upsert(cls, owner_telegram_id: int, **fields: object) -> None:
        """Создаёт или обновляет запись владельца."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == owner_telegram_id).limit(1)

            entity = session.scalar(statement)

            if entity is None:
                entity_fields = {field_name: value for field_name, value in fields.items() if value is not None}
                session.add(cls(owner_telegram_id=owner_telegram_id, **entity_fields))
            else:
                for field_name, value in fields.items():
                    if value is None:
                        continue
                    setattr(entity, field_name, value)

            session.commit()
