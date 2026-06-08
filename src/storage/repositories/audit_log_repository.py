from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.orm.audit_log import AuditLog


class AuditLogRepository(Protocol):
    """Репозиторий пользовательских действий."""

    def add(
        self,
        telegram_id: int,
        user_name: str,
        command: str,
        status: str,
        details: str | None = None,
    ) -> None:
        """Сохраняет запись аудита."""

    def list_recent(self, limit: int = 50) -> list[AuditLog]:
        """Возвращает последние действия пользователей."""

    def clear(self) -> None:
        """Очищает журнал аудита."""


class SQLAlchemyAuditLogRepository(AuditLogRepository):
    """Работает с ORM-моделью AuditLog."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def add(
        self,
        telegram_id: int,
        user_name: str,
        command: str,
        status: str,
        details: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            session.add(
                AuditLog(
                    telegram_id=telegram_id,
                    user_name=user_name,
                    command=command,
                    status=status,
                    details=details,
                )
            )
            session.commit()

    def list_recent(self, limit: int = 50) -> list[AuditLog]:
        with self._session_factory() as session:
            statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)

            return list(session.scalars(statement))

    def clear(self) -> None:
        with self._session_factory() as session:
            session.query(AuditLog).delete()
            session.commit()
