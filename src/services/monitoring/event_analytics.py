"""Минимальная аналитика по app_events для dogfooding."""

from __future__ import annotations

import json

from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB

from src.storage.orm.system.app_events import AppEvent, EventSeverity, EventType


class EventAnalytics:
    """Строит простые агрегаты поверх журнала событий."""

    @classmethod
    def get_total_events(cls) -> int:
        with AppEvent.session() as session:
            statement = select(func.count()).select_from(AppEvent)
            return session.scalar(statement) or 0

    @classmethod
    def get_event_counts(cls) -> dict[str, int]:
        with AppEvent.session() as session:
            statement = select(AppEvent.event_type, func.count().label("count")).group_by(AppEvent.event_type).order_by(AppEvent.event_type.asc())
            return {event_type: count for event_type, count in session.execute(statement).all()}

    @classmethod
    def get_recent_errors(cls, limit: int = 20) -> list[dict[str, object]]:
        with AppEvent.session() as session:
            statement = (
                select(AppEvent)
                .where(AppEvent.event_type == EventType.ERROR.value)
                .where(AppEvent.severity == EventSeverity.ERROR.value)
                .order_by(AppEvent.created_at.desc(), AppEvent.id.desc())
                .limit(limit)
            )
            rows = session.scalars(statement).all()
            return [cls._row_to_error(row) for row in rows]

    @classmethod
    def get_error_counts(cls) -> int:
        with AppEvent.session() as session:
            statement = select(func.count()).select_from(AppEvent).where(AppEvent.event_type == EventType.ERROR.value)
            return session.scalar(statement) or 0

    @classmethod
    def get_document_generation_stats(cls) -> list[dict[str, object]]:
        document_type = func.coalesce(cast(AppEvent.details, JSONB)["document_type"].astext, "unknown")
        with AppEvent.session() as session:
            statement = (
                select(document_type.label("document_type"), func.count().label("count"))
                .where(AppEvent.event_type == EventType.DOCUMENT_GENERATED.value)
                .group_by(document_type)
                .order_by(func.count().desc())
            )
            return [{"document_type": document_type_value, "count": count} for document_type_value, count in session.execute(statement).all()]

    @staticmethod
    def _row_to_error(row: AppEvent) -> dict[str, object]:
        details: dict[str, object] | str | None
        if row.details is None:
            details = None
        else:
            try:
                details = json.loads(row.details)
            except json.JSONDecodeError:
                details = row.details
        return {
            "created_at": row.created_at,
            "event_type": row.event_type,
            "severity": row.severity,
            "details": details,
        }
