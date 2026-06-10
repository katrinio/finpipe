"""ORM-сущность пользовательских настроек."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class UserConfig(BaseModel):
    """Пользовательские настройки, включая Telegram-привязку."""

    # TODO(HIGH):
    # Эта таблица постепенно дублирует профиль пользователя и служебные настройки.
    # Перед следующими фичами нужно решить, какие поля остаются здесь, а какие переезжают в профильные ORM-модели.

    __tablename__ = "user_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
    user_name: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime)

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int) -> UserConfig | None:
        """Возвращает запись пользователя по Telegram id."""

        with cls.session() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def add(cls, telegram_id: int, user_name: str) -> None:
        # TODO(MEDIUM):
        # CRUD-операции здесь отличаются от остальных ORM-моделей.
        # Нужен единый контракт `create/get/update/upsert/delete` для всего storage-слоя.
        with cls.session() as session:
            statement = select(UserConfig).where(UserConfig.telegram_id == telegram_id).limit(1)
            user = session.execute(statement).scalar_one_or_none()

            if user is None:
                user = UserConfig(telegram_id=telegram_id, user_name=user_name)
                session.add(user)
            else:
                user.user_name = user_name

            session.commit()
