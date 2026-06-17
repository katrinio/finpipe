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


def test_bot_started_notification_is_sent_to_monitoring_chat(monkeypatch) -> None:
    monkeypatch.delenv("MONITORING_CHAT_ID", raising=False)
    monkeypatch.setenv("BOT_OWNER_TELEGRAM_ID", "777")

    telegram = FakeTelegramClient()
    monkeypatch.setattr(EventLogger, "_handlers", [])
    monkeypatch.setattr(app_events.AppEvent, "create", classmethod(lambda cls, **kwargs: None))

    register_monitoring_notifications(telegram)

    EventLogger.log(EventType.BOT_STARTED, EventSeverity.INFO, {"component": "telegram_bot"})

    assert telegram.sent_messages_with_chat_ids[-1] == (
        777,
        'Monitoring event: bot_started\nSeverity: info\nDetails: {"component":"telegram_bot"}',
    )


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

    EventLogger.log(EventType.BOT_STARTED, EventSeverity.INFO)

    assert len(calls) == 1
