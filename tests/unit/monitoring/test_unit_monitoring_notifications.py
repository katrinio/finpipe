from src.services.monitoring.event_logger import EventLogger
from src.services.monitoring.notifications import get_monitoring_chat_id, register_monitoring_notifications
from src.storage.orm.system import app_events
from src.storage.orm.system.app_events import EventSeverity, EventType
from tests.fakes.fake_telegram import FakeTelegramClient


def test_monitoring_chat_id_uses_explicit_setting(monkeypatch) -> None:
    monkeypatch.setenv("MONITORING_CHAT_ID", "555")
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    assert get_monitoring_chat_id() == 555


def test_monitoring_chat_id_falls_back_to_owner(monkeypatch) -> None:
    monkeypatch.delenv("MONITORING_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    assert get_monitoring_chat_id() == 777


def test_backup_failed_is_sent_to_monitoring_chat(monkeypatch) -> None:
    monkeypatch.delenv("MONITORING_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    telegram = FakeTelegramClient()
    monkeypatch.setattr(EventLogger, "_handlers", [])
    monkeypatch.setattr(app_events.AppEvent, "create", classmethod(lambda cls, **kwargs: None))

    register_monitoring_notifications(telegram)

    EventLogger.log(EventType.BACKUP_FAILED, EventSeverity.ERROR, {"error": "pg_dump failed"})

    assert len(telegram.sent_messages_with_chat_ids) == 1
    chat_id, text = telegram.sent_messages_with_chat_ids[0]
    assert chat_id == 777
    assert "backup_failed" in text


def test_bot_started_is_not_sent_to_monitoring_chat(monkeypatch) -> None:
    monkeypatch.delenv("MONITORING_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    telegram = FakeTelegramClient()
    monkeypatch.setattr(EventLogger, "_handlers", [])
    monkeypatch.setattr(app_events.AppEvent, "create", classmethod(lambda cls, **kwargs: None))

    register_monitoring_notifications(telegram)

    EventLogger.log(EventType.BOT_STARTED, EventSeverity.WARNING, {"component": "telegram_bot"})

    assert telegram.sent_messages == []


def test_non_critical_events_are_not_sent_to_chat(monkeypatch) -> None:
    monkeypatch.delenv("MONITORING_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    telegram = FakeTelegramClient()
    monkeypatch.setattr(EventLogger, "_handlers", [])
    monkeypatch.setattr(app_events.AppEvent, "create", classmethod(lambda cls, **kwargs: None))

    register_monitoring_notifications(telegram)

    for event_type in (EventType.DOCUMENT_GENERATED, EventType.DOCUMENT_GENERATION_FAILED, EventType.ERROR):
        EventLogger.log(event_type, EventSeverity.ERROR, None)

    assert telegram.sent_messages == []


def test_monitoring_handler_does_not_recurse_on_send_failure(monkeypatch) -> None:
    """Ошибка при отправке уведомления не должна повторно вызывать EventLogger."""

    monkeypatch.delenv("MONITORING_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    calls: list[str] = []

    class FailingTelegram:
        def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
            calls.append(text)
            raise RuntimeError("network error")

    monkeypatch.setattr(EventLogger, "_handlers", [])
    monkeypatch.setattr(app_events.AppEvent, "create", classmethod(lambda cls, **kwargs: None))

    register_monitoring_notifications(FailingTelegram())  # type: ignore[arg-type]

    EventLogger.log(EventType.BACKUP_FAILED, EventSeverity.ERROR)

    assert len(calls) == 1
