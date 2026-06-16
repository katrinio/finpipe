"""Сервис записи системных событий в app_events."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, ClassVar

from src.storage.orm.system.app_events import AppEvent, EventSeverity, EventType

logger = logging.getLogger(__name__)


class EventLogger:
    """Минимальный логгер событий, не знающий ничего о SQLAlchemy Session."""

    _handlers: ClassVar[list[Callable[[EventType, EventSeverity, str | None], None]]] = []

    @staticmethod
    def log(
        event_type: EventType,
        severity: EventSeverity,
        details: str | dict[str, Any] | None = None,
    ) -> None:
        serialized_details = EventLogger._serialize_details(details)
        try:
            AppEvent.create(
                event_type=event_type,
                severity=severity,
                details=serialized_details,
            )
        except Exception:
            logger.exception("Failed to save app event: %s", event_type.value)
            return

        EventLogger._notify_handlers(event_type, severity, serialized_details)

    @staticmethod
    def log_exception(
        exc: Exception,
        details: str | dict[str, Any] | None = None,
    ) -> None:
        message = f"{type(exc).__name__}: {exc}"
        if details:
            prefix = EventLogger._serialize_details(details)
            message = f"{prefix}. {message}" if prefix else message

        EventLogger.log(
            EventType.ERROR,
            EventSeverity.ERROR,
            message,
        )

    @staticmethod
    def _serialize_details(details: str | dict[str, Any] | None) -> str | None:
        if details is None:
            return None
        if isinstance(details, str):
            return details
        return json.dumps(details, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def register_handler(
        cls,
        handler: Callable[[EventType, EventSeverity, str | None], None],
    ) -> None:
        cls._handlers.append(handler)

    @classmethod
    def _notify_handlers(
        cls,
        event_type: EventType,
        severity: EventSeverity,
        details: str | None,
    ) -> None:
        for handler in cls._handlers:
            try:
                handler(event_type, severity, details)
            except Exception:
                logger.exception("EventLogger handler failed")
