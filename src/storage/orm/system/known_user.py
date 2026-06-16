"""ORM-модель пользователя, уже взаимодействовавшего с Telegram-ботом."""

from datetime import datetime

from sqlalchemy import String, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, DateTime

from src.storage.orm.base import BaseModel, current_utc_timestamp


class KnownUser(BaseModel):
    """Хранит сведения о Telegram-пользователе без выдачи прав доступа."""

    __tablename__ = "known_users"

    telegram_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> "KnownUser | None":
        """Возвращает известного пользователя по Telegram ID."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def upsert(cls, telegram_id: int, username: str | None, first_name: str | None) -> None:
        """Создаёт или обновляет запись известного Telegram-пользователя."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            entity = session.scalar(statement)
            current_time = current_utc_timestamp()

            if entity is None:
                session.add(
                    cls(
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        created_at=current_time,
                        last_seen_at=current_time,
                    )
                )
            else:
                entity.username = username
                entity.first_name = first_name
                entity.last_seen_at = current_time

            session.commit()

    @classmethod
    def list_all(cls) -> list["KnownUser"]:
        """Возвращает всех известных пользователей."""

        with cls.session() as session:
            statement = select(cls).order_by(cls.last_seen_at.desc(), cls.telegram_id.asc())
            return list(session.scalars(statement))
