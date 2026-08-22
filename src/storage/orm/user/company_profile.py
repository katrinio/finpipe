"""ORM-модель профиля компании пользователя."""

from datetime import datetime

from sqlalchemy import Integer, String, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, DateTime

from src.storage.exceptions import StorageRecordNotFoundError
from src.storage.orm.base import BaseModel


class CompanyProfile(BaseModel):
    """Хранит компанию и платёжные реквизиты пользователя."""

    __tablename__ = "company_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_telegram_id: Mapped[int] = mapped_column(BIGINT, nullable=False, unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String)
    company_address: Mapped[str] = mapped_column(String)
    registration_number: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_number: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_code: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_description: Mapped[str | None] = mapped_column(String, nullable=True)
    service_agreement_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> CompanyProfile | None:
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
    def update(cls, owner_telegram_id: int, **fields: object) -> None:
        """Обновляет поля записи владельца."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == owner_telegram_id).limit(1)
            entity = session.scalar(statement)

            if entity is None:
                raise StorageRecordNotFoundError(f"{cls.__name__} for owner {owner_telegram_id} not found")

            for field_name, value in fields.items():
                setattr(entity, field_name, value)

            session.commit()

    @classmethod
    def upsert(
        cls,
        owner_telegram_id: int,
        **fields: object,
    ) -> None:
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
