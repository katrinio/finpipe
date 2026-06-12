"""ORM-модель подключения Gmail пользователя."""

from datetime import datetime

from sqlalchemy import Integer, String, func, select, update
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel, current_utc_timestamp


class GmailAccount(BaseModel):
    """Хранит состояние подключения Gmail для Telegram-пользователя."""

    __tablename__ = "gmail_account"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    owner_telegram_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    gmail_email: Mapped[str | None] = mapped_column(String, nullable=True)
    gmail_refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    gmail_connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    gmail_last_error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> GmailAccount | None:
        """Возвращает Gmail-настройки пользователя."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def exists(cls, owner_telegram_id: int) -> bool:
        """Проверяет наличие записи Gmail для пользователя."""

        return cls.get_by_owner(owner_telegram_id) is not None

    @classmethod
    def update_gmail_credentials(cls, telegram_id: int, gmail_email: str, gmail_refresh_token: str) -> None:
        """Сохраняет токен и метаданные успешного Gmail-подключения."""

        with cls.session() as session:
            session.execute(
                update(cls)
                .where(cls.owner_telegram_id == telegram_id)
                .values(
                    gmail_refresh_token=gmail_refresh_token,
                    gmail_email=gmail_email,
                    gmail_connected_at=current_utc_timestamp(),
                    gmail_last_error=None,
                )
            )
            session.commit()

    @classmethod
    def clear_gmail_credentials(cls, telegram_id: int) -> None:
        """Очищает сохранённые Gmail-учётные данные пользователя."""

        with cls.session() as session:
            session.execute(
                update(cls)
                .where(cls.owner_telegram_id == telegram_id)
                .values(
                    gmail_refresh_token=None,
                    gmail_email=None,
                    gmail_connected_at=None,
                    gmail_last_error=None,
                )
            )
            session.commit()

    @classmethod
    def has_gmail_connection(cls, telegram_id: int) -> bool:
        """Проверяет, подключён ли Gmail для пользователя."""

        user_config = cls.get_by_owner(telegram_id)
        return bool(user_config and user_config.gmail_refresh_token)

    @classmethod
    def set_gmail_connection_error(cls, telegram_id: int, error_message: str) -> None:
        """Сохраняет последнюю ошибку Gmail-подключения."""

        with cls.session() as session:
            session.execute(update(cls).where(cls.owner_telegram_id == telegram_id).values(gmail_last_error=error_message))
            session.commit()
