"""Доставка мониторинговых уведомлений в Telegram."""

from __future__ import annotations

from dataclasses import dataclass

from src.integrations.telegram.client import TelegramClient
from src.storage.orm.system.app_events import EventSeverity, EventType
from src.utils.credentials import EnvVar


def get_monitoring_chat_id() -> int:
    """Возвращает чат для мониторинговых уведомлений."""

    monitoring_chat_id = EnvVar.get_optional_env("MONITORING_CHAT_ID", "")
    if monitoring_chat_id:
        return int(monitoring_chat_id)

    return int(EnvVar.get_required_env("BOT_OWNER_TELEGRAM_ID"))


def send_monitoring_message(telegram: TelegramClient, text: str) -> None:
    """Отправляет мониторинговое сообщение в выделенный чат."""

    telegram.send_message(get_monitoring_chat_id(), text)


@dataclass(frozen=True)
class MonitoringEvent:
    event_type: EventType
    severity: EventSeverity
    details: str | None

    def format_message(self) -> str:
        lines = [f"Monitoring event: {self.event_type.value}", f"Severity: {self.severity.value}"]
        if self.details:
            lines.append(f"Details: {self.details}")
        return "\n".join(lines)


def build_monitoring_message(event_type: EventType, severity: EventSeverity, details: str | None) -> str:
    """Формирует текст уведомления для мониторингового чата."""

    return MonitoringEvent(event_type=event_type, severity=severity, details=details).format_message()


def register_monitoring_notifications(telegram: TelegramClient) -> None:
    """Подключает отправку мониторинговых уведомлений к EventLogger."""

    from src.services.monitoring.event_logger import EventLogger

    def handler(event_type: EventType, severity: EventSeverity, details: str | None) -> None:
        send_monitoring_message(telegram, build_monitoring_message(event_type, severity, details))

    EventLogger.register_handler(handler)
