"""ORM-сущность для OAuth state сессий."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, select, update
from sqlalchemy.orm import Mapped, mapped_column

from src.storage.orm.base import BaseModel, current_utc_timestamp, normalize_timestamp


class OAuthSession(BaseModel):
    __tablename__ = "oauth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String, nullable=True)
    purpose: Mapped[str] = mapped_column(String, nullable=False, default="gmail_connect")
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @classmethod
    def create(
        cls,
        telegram_id: int,
        telegram_username: str | None,
        state: str,
        expires_at: datetime,
    ) -> "OAuthSession":
        with cls.session() as session:
            oauth_session = cls(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                state=state,
                purpose="gmail_connect",
                status="pending",
                created_at=current_utc_timestamp(),
                expires_at=normalize_timestamp(expires_at),
            )
            session.add(oauth_session)
            session.commit()
            return oauth_session

    @classmethod
    def get_by_state(cls, state: str) -> "OAuthSession | None":
        with cls.session() as session:
            statement = select(cls).where(cls.state == state).limit(1)
            return session.scalar(statement)

    @classmethod
    def get_active_by_telegram_id(cls, telegram_id: int) -> "OAuthSession | None":
        with cls.session() as session:
            statement = select(cls).where(cls.telegram_id == telegram_id).where(cls.status == "pending").order_by(cls.created_at.desc()).limit(1)
            return session.scalar(statement)

    @classmethod
    def mark_used(cls, state: str) -> None:
        with cls.session() as session:
            session.execute(update(cls).where(cls.state == state).values(status="used", used_at=current_utc_timestamp()))
            session.commit()

    @classmethod
    def mark_failed(cls, state: str, error_message: str) -> None:
        with cls.session() as session:
            session.execute(update(cls).where(cls.state == state).values(status="failed", error_message=error_message))
            session.commit()

    @classmethod
    def mark_expired(cls, state: str) -> None:
        with cls.session() as session:
            session.execute(update(cls).where(cls.state == state).values(status="expired"))
            session.commit()

    @classmethod
    def cleanup_expired(cls) -> int:
        with cls.session() as session:
            statement = select(cls).where(cls.expires_at < current_utc_timestamp())
            expired_sessions = list(session.scalars(statement))
            for oauth_session in expired_sessions:
                oauth_session.status = "expired"
            session.commit()
            return len(expired_sessions)
