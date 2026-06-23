"""Аналитика по app_events для мониторингового чата."""

from __future__ import annotations

import json

from sqlalchemy import select

from src.storage.orm.system.app_events import AppEvent, EventSeverity


class EventAnalytics:
    """Строит агрегаты поверх журнала событий."""

    @classmethod
    def get_recent_errors(cls, limit: int = 20) -> list[dict[str, object]]:
        with AppEvent.session() as session:
            statement = (
                select(AppEvent)
                .where(AppEvent.severity == EventSeverity.ERROR.value)
                .order_by(AppEvent.created_at.desc(), AppEvent.id.desc())
                .limit(limit)
            )
            rows = session.scalars(statement).all()
            return [cls._row_to_error(row) for row in rows]

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
