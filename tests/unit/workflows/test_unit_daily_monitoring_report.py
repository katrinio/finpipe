from datetime import UTC, datetime, timedelta
from typing import cast

from src.integrations.telegram.client import TelegramClient
from src.storage.orm.database import Database
from src.storage.orm.system.app_events import AppEvent, EventSeverity, EventType
from src.workflows.monitoring import daily_report
from tests.fakes.fake_telegram import FakeTelegramClient
from tests.helpers.database import build_test_database_url, initialize_test_database


def _build_database(tmp_path) -> Database:
    database = Database(build_test_database_url(tmp_path / "test.db"))
    initialize_test_database(database)
    return database


def _create_event(database: Database, *, created_at: datetime, event_type: EventType, severity: EventSeverity, details: str | None = None) -> None:
    database.bind_models()
    with AppEvent.session() as session:
        session.add(
            AppEvent(
                created_at=created_at,
                event_type=event_type.value,
                severity=severity.value,
                details=details,
            )
        )
        session.commit()


def test_daily_monitoring_summary_uses_last_24_hours(tmp_path) -> None:
    database = _build_database(tmp_path)
    now = datetime(2026, 6, 17, 7, 0, tzinfo=UTC)
    _create_event(database, created_at=now - timedelta(hours=23), event_type=EventType.BOT_STARTED, severity=EventSeverity.INFO)
    _create_event(database, created_at=now - timedelta(hours=25), event_type=EventType.ERROR, severity=EventSeverity.ERROR)

    summary = daily_report.load_daily_monitoring_summary(now=now)

    assert summary.total_events == 1
    assert summary.error_events == 0
    assert summary.event_type_counts == {EventType.BOT_STARTED.value: 1}


def test_daily_monitoring_summary_groups_by_severity_and_event_type(tmp_path) -> None:
    database = _build_database(tmp_path)
    now = datetime(2026, 6, 17, 7, 0, tzinfo=UTC)
    _create_event(database, created_at=now - timedelta(hours=1), event_type=EventType.BOT_STARTED, severity=EventSeverity.INFO)
    _create_event(database, created_at=now - timedelta(hours=2), event_type=EventType.ERROR, severity=EventSeverity.ERROR)
    _create_event(
        database,
        created_at=now - timedelta(hours=3),
        event_type=EventType.DOCUMENT_GENERATION_FAILED,
        severity=EventSeverity.ERROR,
    )

    summary = daily_report.load_daily_monitoring_summary(now=now)

    assert summary.severity_counts == {EventSeverity.ERROR.value: 2, EventSeverity.INFO.value: 1}
    assert summary.event_type_counts == {
        EventType.BOT_STARTED.value: 1,
        EventType.DOCUMENT_GENERATION_FAILED.value: 1,
        EventType.ERROR.value: 1,
    }


def test_format_daily_monitoring_summary_without_events() -> None:
    summary = daily_report.DailyMonitoringSummary(
        period_start=datetime(2026, 6, 16, 7, 0, tzinfo=UTC),
        period_end=datetime(2026, 6, 17, 7, 0, tzinfo=UTC),
        total_events=0,
        error_events=0,
        severity_counts={},
        event_type_counts={},
        recent_errors=[],
        infrastructure=daily_report.InfrastructureSummary(
            database_status="OK",
            disk_usage_percent=83,
            certificate=daily_report.CertificateStatus(expires_at=None, days_remaining=None, status_emoji="unknown"),
        ),
    )

    text = daily_report.format_daily_monitoring_summary(summary)

    assert "Events: 0" in text
    assert "Errors: 0" in text
    assert "- none" in text
    assert "Infrastructure:" in text
    assert "Database: OK" in text
    assert "Disk usage: 83%" in text
    assert "SSL certificate: unknown" in text


def test_format_daily_monitoring_summary_with_errors() -> None:
    summary = daily_report.DailyMonitoringSummary(
        period_start=datetime(2026, 6, 16, 7, 0, tzinfo=UTC),
        period_end=datetime(2026, 6, 17, 7, 0, tzinfo=UTC),
        total_events=2,
        error_events=1,
        severity_counts={EventSeverity.ERROR.value: 1, EventSeverity.INFO.value: 1},
        event_type_counts={EventType.ERROR.value: 1, EventType.BOT_STARTED.value: 1},
        recent_errors=[
            daily_report.MonitoringEventRow(
                created_at=datetime(2026, 6, 17, 6, 55, tzinfo=UTC),
                event_type=EventType.ERROR.value,
                severity=EventSeverity.ERROR.value,
                details="boom",
            )
        ],
        infrastructure=daily_report.InfrastructureSummary(
            database_status="OK",
            disk_usage_percent=83,
            certificate=daily_report.CertificateStatus(
                expires_at=datetime(2026, 8, 23, 7, 0, tzinfo=UTC),
                days_remaining=67,
                status_emoji="✅",
            ),
        ),
    )

    text = daily_report.format_daily_monitoring_summary(summary)

    assert "Recent errors:" in text
    assert "error | boom" in text
    assert "SSL certificate: 67 days remaining ✅" in text


def test_daily_monitoring_summary_sends_to_monitoring_chat(monkeypatch) -> None:
    telegram = FakeTelegramClient()
    summary = daily_report.DailyMonitoringSummary(
        period_start=datetime(2026, 6, 16, 7, 0, tzinfo=UTC),
        period_end=datetime(2026, 6, 17, 7, 0, tzinfo=UTC),
        total_events=0,
        error_events=0,
        severity_counts={},
        event_type_counts={},
        recent_errors=[],
        infrastructure=daily_report.InfrastructureSummary(
            database_status="OK",
            disk_usage_percent=83,
            certificate=daily_report.CertificateStatus(expires_at=None, days_remaining=None, status_emoji="unknown"),
        ),
    )
    monkeypatch.setattr(daily_report, "get_monitoring_chat_id", lambda: 555)

    daily_report.send_daily_monitoring_summary(cast(TelegramClient, telegram), summary)

    assert telegram.sent_messages_with_chat_ids == [(555, daily_report.format_daily_monitoring_summary(summary))]


def test_daily_monitoring_summary_does_not_depend_on_telegram_update(monkeypatch) -> None:
    telegram = FakeTelegramClient()
    monkeypatch.setattr(
        daily_report,
        "load_daily_monitoring_summary",
        lambda now=None, recent_error_limit=5: daily_report.DailyMonitoringSummary(
            period_start=datetime(2026, 6, 16, 7, 0, tzinfo=UTC),
            period_end=datetime(2026, 6, 17, 7, 0, tzinfo=UTC),
            total_events=0,
            error_events=0,
            severity_counts={},
            event_type_counts={},
            recent_errors=[],
            infrastructure=daily_report.InfrastructureSummary(
                database_status="OK",
                disk_usage_percent=83,
                certificate=daily_report.CertificateStatus(expires_at=None, days_remaining=None, status_emoji="unknown"),
            ),
        ),
    )
    monkeypatch.setattr(daily_report, "send_daily_monitoring_summary", lambda telegram_client, summary: telegram_client.send_message(1, "ok"))
    monkeypatch.setattr(daily_report, "TelegramClient", lambda: telegram)

    assert daily_report.main() == 0
    assert telegram.sent_messages_with_chat_ids == [(1, "ok")]


def test_certificate_status_emoji_thresholds() -> None:
    assert daily_report._certificate_status_emoji(31) == "✅"
    assert daily_report._certificate_status_emoji(30) == "⚠️"
    assert daily_report._certificate_status_emoji(8) == "⚠️"
    assert daily_report._certificate_status_emoji(7) == "🚨"


def test_certificate_days_remaining_calculation(monkeypatch) -> None:
    monkeypatch.setattr(daily_report, "_get_monitoring_domain", lambda: "finpipe.example")
    monkeypatch.setattr(
        daily_report,
        "_get_certificate_expiry",
        lambda domain: datetime(2026, 8, 23, 7, 0, tzinfo=UTC),
    )

    certificate = daily_report.load_certificate_status()

    assert certificate.days_remaining == 67
    assert certificate.status_emoji == "✅"


def test_infrastructure_block_handles_certificate_and_db_failures(monkeypatch) -> None:
    monkeypatch.setattr(daily_report, "_get_monitoring_domain", lambda: "finpipe.example")
    monkeypatch.setattr(daily_report, "_get_certificate_expiry", lambda domain: (_ for _ in ()).throw(RuntimeError("tls error")))
    monkeypatch.setattr(daily_report.AppEvent, "session", lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    infrastructure = daily_report.load_infrastructure_summary()

    assert infrastructure.database_status == "ERROR"
    assert infrastructure.certificate.days_remaining is None
    assert infrastructure.certificate.status_emoji == "unknown"
