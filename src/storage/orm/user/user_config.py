from datetime import datetime

from sqlalchemy import Float, Integer, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class UserConfig(BaseModel):
    """Хранит пользовательские настройки Telegram-аккаунта."""

    __tablename__ = "user_config"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_amount_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    received_amount_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    exchange_amount_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    @classmethod
    def get_by_owner(cls, telegram_id: int) -> "UserConfig | None":
        """Возвращает настройки пользователя."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)

            return session.scalar(statement)

    @classmethod
    def get_or_create(cls, telegram_id: int) -> "UserConfig":
        """Возвращает настройки пользователя, создавая запись при необходимости."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            config = session.scalar(statement)

            if config is None:
                config = cls(telegram_id=telegram_id)
                session.add(config)
                session.commit()

            return config

    @classmethod
    def upsert(
        cls,
        telegram_id: int,
        invoice_amount_eur: int | None = None,
        received_amount_eur: float | None = None,
        exchange_amount_eur: float | None = None,
    ) -> None:
        """Создаёт или обновляет настройки пользователя."""

        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).limit(1)
            config = session.scalar(statement)

            resolved_exchange_amount = exchange_amount_eur
            if resolved_exchange_amount is None and received_amount_eur is not None:
                resolved_exchange_amount = received_amount_eur

            if config is None:
                config = cls(
                    telegram_id=telegram_id,
                    invoice_amount_eur=invoice_amount_eur,
                    received_amount_eur=received_amount_eur,
                    exchange_amount_eur=resolved_exchange_amount,
                )
                session.add(config)
            else:
                if invoice_amount_eur is not None:
                    config.invoice_amount_eur = invoice_amount_eur
                if received_amount_eur is not None:
                    config.received_amount_eur = received_amount_eur
                if resolved_exchange_amount is not None:
                    config.exchange_amount_eur = resolved_exchange_amount

            session.commit()
