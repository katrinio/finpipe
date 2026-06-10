from datetime import datetime

from sqlalchemy import Integer, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, String

from src.storage.orm.base import BaseModel


class UserStateStorage(BaseModel):
    """Обработанный User State в Боте."""

    __tablename__ = "user_state_storage"
    __pk_column_name__ = "id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> UserStateStorage | None:
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
