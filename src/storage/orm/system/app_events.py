from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Text

from src.storage.orm.base import BaseModel


class EventType(StrEnum):
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"

    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    USER_AUTHORIZED = "user_authorized"

    ERROR = "error"


class EventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AppEvent(BaseModel):
    __tablename__ = "app_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        severity: EventSeverity,
        details: str | None = None,
    ) -> "AppEvent":
        event = cls(
            event_type=event_type.value,
            severity=severity.value,
            details=details,
        )

        with cls.session() as session:
            session.add(event)
            session.commit()

        return event
