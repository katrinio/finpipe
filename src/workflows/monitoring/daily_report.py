"""Daily monitoring summary for production data."""

from __future__ import annotations

import shutil
import socket
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from sqlalchemy import func, select

from src.integrations.telegram.client import TelegramClient
from src.services.monitoring.notifications import get_monitoring_chat_id
from src.storage.orm.system.app_events import AppEvent
from src.utils.credentials import LOGGER, EnvVar


@dataclass(frozen=True)
class MonitoringEventRow:
    created_at: datetime
    event_type: str
    severity: str
    details: str | None


@dataclass(frozen=True)
class DailyMonitoringSummary:
    period_start: datetime
    period_end: datetime
    total_events: int
    error_events: int
    severity_counts: dict[str, int]
    event_type_counts: dict[str, int]
    recent_errors: list[MonitoringEventRow]
    infrastructure: "InfrastructureSummary"


@dataclass(frozen=True)
class CertificateStatus:
    expires_at: datetime | None
    days_remaining: int | None
    status_emoji: str


@dataclass(frozen=True)
class InfrastructureSummary:
    database_status: str
    disk_usage_percent: int | None
    certificate: CertificateStatus


def get_report_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    end = now or datetime.now(UTC)
    start = end - timedelta(hours=24)
    return start, end


def load_daily_monitoring_summary(now: datetime | None = None, recent_error_limit: int = 5) -> DailyMonitoringSummary:
    period_start, period_end = get_report_window(now)

    base_filter = (AppEvent.created_at >= period_start) & (AppEvent.created_at <= period_end)
    total_events = 0
    error_events = 0
    severity_counts: dict[str, int] = {}
    event_type_counts: dict[str, int] = {}
    recent_errors: list[MonitoringEventRow] = []

    with AppEvent.session() as session:
        total_events = session.scalar(select(func.count()).select_from(AppEvent).where(base_filter)) or 0
        error_events = session.scalar(select(func.count()).select_from(AppEvent).where(base_filter).where(AppEvent.severity == "error")) or 0

        severity_counts = {
            severity: count
            for severity, count in session.execute(
                select(AppEvent.severity, func.count().label("count"))
                .where(base_filter)
                .group_by(AppEvent.severity)
                .order_by(AppEvent.severity.asc())
            ).all()
        }
        event_type_counts = {
            event_type: count
            for event_type, count in session.execute(
                select(AppEvent.event_type, func.count().label("count"))
                .where(base_filter)
                .group_by(AppEvent.event_type)
                .order_by(func.count().desc(), AppEvent.event_type.asc())
            ).all()
        }
        recent_errors = [
            MonitoringEventRow(
                created_at=row.created_at,
                event_type=row.event_type,
                severity=row.severity,
                details=row.details,
            )
            for row in session.scalars(
                select(AppEvent)
                .where(base_filter)
                .where(AppEvent.severity == "error")
                .order_by(AppEvent.created_at.desc(), AppEvent.id.desc())
                .limit(recent_error_limit)
            ).all()
        ]

    return DailyMonitoringSummary(
        period_start=period_start,
        period_end=period_end,
        total_events=total_events,
        error_events=error_events,
        severity_counts=severity_counts,
        event_type_counts=event_type_counts,
        recent_errors=recent_errors,
        infrastructure=load_infrastructure_summary(),
    )


def format_daily_monitoring_summary(summary: DailyMonitoringSummary) -> str:
    lines = [
        "📊 Finpipe Daily Report",
        "",
        "Period:",
        f"{summary.period_start.strftime('%Y-%m-%d %H:%M')} → {summary.period_end.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Events: {summary.total_events}",
        f"Errors: {summary.error_events}",
        "",
        "Severity:",
    ]
    lines.extend(_format_counts(summary.severity_counts))
    lines.append("")
    lines.append("Top events:")
    lines.extend(_format_counts(summary.event_type_counts))
    lines.append("")
    lines.append("Infrastructure:")
    lines.append(f"Database: {summary.infrastructure.database_status}")
    lines.append(
        f"Disk usage: {summary.infrastructure.disk_usage_percent}%"
        if summary.infrastructure.disk_usage_percent is not None
        else "Disk usage: unknown"
    )
    cert = summary.infrastructure.certificate
    if cert.days_remaining is None:
        lines.append("SSL certificate: unknown")
    else:
        lines.append(f"SSL certificate: {cert.days_remaining} days remaining {cert.status_emoji}")

    if summary.recent_errors:
        lines.append("")
        lines.append("Recent errors:")
        for row in summary.recent_errors:
            details = f" | {row.details}" if row.details else ""
            lines.append(f"- {row.created_at.strftime('%Y-%m-%d %H:%M')} {row.event_type}{details}")

    return "\n".join(lines)


def send_daily_monitoring_summary(telegram: TelegramClient, summary: DailyMonitoringSummary) -> None:
    telegram.send_message(get_monitoring_chat_id(), format_daily_monitoring_summary(summary))


def main() -> int:
    EnvVar.load_dotenv()
    try:
        summary = load_daily_monitoring_summary()
        send_daily_monitoring_summary(TelegramClient(), summary)
    except Exception:
        LOGGER.exception("Daily monitoring summary failed.")
        return 1
    return 0


def _format_counts(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {key}: {value}" for key, value in counts.items()]


def load_infrastructure_summary() -> InfrastructureSummary:
    database_status = "OK"
    try:
        with AppEvent.session() as session:
            session.execute(select(1))
    except Exception:
        database_status = "ERROR"

    disk_usage = None
    try:
        disk_usage = int(shutil.disk_usage(Path("/")).used * 100 / shutil.disk_usage(Path("/")).total)
    except Exception:
        disk_usage = None

    certificate = load_certificate_status()
    return InfrastructureSummary(database_status=database_status, disk_usage_percent=disk_usage, certificate=certificate)


def load_certificate_status() -> CertificateStatus:
    domain = _get_monitoring_domain()
    if not domain:
        return CertificateStatus(expires_at=None, days_remaining=None, status_emoji="unknown")

    try:
        expires_at = _get_certificate_expiry(domain)
    except Exception:
        return CertificateStatus(expires_at=None, days_remaining=None, status_emoji="unknown")

    days_remaining = max(0, (expires_at.date() - datetime.now(UTC).date()).days)
    return CertificateStatus(
        expires_at=expires_at,
        days_remaining=days_remaining,
        status_emoji=_certificate_status_emoji(days_remaining),
    )


def _get_certificate_expiry(domain: str) -> datetime:
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=5) as sock, context.wrap_socket(sock, server_hostname=domain) as secure_sock:
        certificate = cast(dict[str, str], secure_sock.getpeercert())
    not_after = certificate["notAfter"]
    return datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)


def _certificate_status_emoji(days_remaining: int) -> str:
    if days_remaining > 30:
        return "✅"
    if days_remaining >= 8:
        return "⚠️"
    return "🚨"


def _get_monitoring_domain() -> str | None:
    for env_name in ("FINPIPE_DOMAIN", "APP_DOMAIN", "DOMAIN", "PUBLIC_DOMAIN"):
        value = EnvVar.get_optional_env(env_name, "").strip()
        if value:
            return value
    return None


if __name__ == "__main__":
    raise SystemExit(main())
