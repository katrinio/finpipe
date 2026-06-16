"""ORM-модель текущего Telegram-состояния пользователя."""

from datetime import datetime

from sqlalchemy import Integer, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, DateTime, Enum

from src.integrations.telegram.states import UserState
from src.storage.orm.base import BaseModel


class UserStateStorage(BaseModel):
    """Хранит текущее Telegram-состояние пользователя."""

    __tablename__ = "user_state_storage"
    __pk_column_name__ = "id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_telegram_id: Mapped[int] = mapped_column(BIGINT, nullable=False, unique=True, index=True)
    state: Mapped[UserState] = mapped_column(Enum(UserState), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(), nullable=True, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> UserStateStorage | None:
        """Возвращает сохранённое состояние пользователя."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def exists(cls, owner_telegram_id: int) -> bool:
        """Проверяет наличие сохранённого состояния."""

        return cls.get_by_owner(owner_telegram_id) is not None

    @classmethod
    def delete(cls, owner_telegram_id: int) -> None:
        """Удаляет сохранённое состояние пользователя."""

        with cls.session() as session:
            statement = delete(cls).where(cls.owner_telegram_id == owner_telegram_id)
            session.execute(statement)
            session.commit()

    @classmethod
    def upsert(cls, owner_telegram_id: int, **fields: object) -> None:
        """Создаёт или обновляет состояние пользователя."""

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
