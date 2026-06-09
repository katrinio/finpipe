"""ORM-сущность пользовательских настроек."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, select, update
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class UserConfig(BaseModel):
    """Пользовательские настройки, включая Telegram-привязку."""

    __tablename__ = "user_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
    user_name: Mapped[str] = mapped_column(String)
    account_holder: Mapped[str] = mapped_column(String)
    account_holder_email: Mapped[str] = mapped_column(String)
    account_holder_address: Mapped[str] = mapped_column(String)
    bank_name: Mapped[str] = mapped_column(String)
    account_number: Mapped[str] = mapped_column(String)
    iban: Mapped[str] = mapped_column(String)
    bic: Mapped[str] = mapped_column(String)
    company_name: Mapped[str] = mapped_column(String)
    company_address: Mapped[str] = mapped_column(String)
    service_agreement_date: Mapped[datetime] = mapped_column(DateTime)
    signature_path: Mapped[str] = mapped_column(String)
    gmail_email: Mapped[str | None] = mapped_column(String, nullable=True)
    gmail_refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    gmail_connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    gmail_last_error: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime)

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> UserConfig | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def add(cls, telegram_id: int, user_name: str) -> None:
        with cls.session() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            user = session.execute(statement).scalar_one_or_none()

            if user is None:
                user = UserConfig(telegram_id=telegram_id, user_name=user_name)
                session.add(user)
            else:
                user.user_name = user_name

            session.commit()

    @classmethod
    def update_gmail_credentials(cls, telegram_id: int, gmail_email: str, gmail_refresh_token: str) -> None:
        with cls.session() as session:
            session.execute(
                update(cls)
                .where(cls.telegram_id == telegram_id)
                .values(
                    gmail_refresh_token=gmail_refresh_token,
                    gmail_email=gmail_email,
                    gmail_connected_at=datetime.utcnow(),
                    gmail_last_error=None,
                )
            )
            session.commit()

    @classmethod
    def clear_gmail_credentials(cls, telegram_id: int) -> None:
        with cls.session() as session:
            session.execute(
                update(cls)
                .where(cls.telegram_id == telegram_id)
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
        user_config = cls.get_by_telegram_id(telegram_id)
        return bool(user_config and user_config.gmail_refresh_token)

    @classmethod
    def set_gmail_connection_error(cls, telegram_id: int, error_message: str) -> None:
        with cls.session() as session:
            session.execute(update(cls).where(cls.telegram_id == telegram_id).values(gmail_last_error=error_message))
            session.commit()
