from __future__ import annotations

from enum import StrEnum

from src.storage.orm.audit_log import AuditLog


class Cmd(StrEnum):
    STATUS = "/status"
    HELP = "/help"
    HEALTH = "/health"
    INVOICE = "/invoice"
    ABOUT = "/about"
    WHOAMI = "/whoami"
    LAST_ACTION = "/last_action"
    CONNECT_GMAIL = "/connect_gmail"
    GMAIL_STATUS = "/gmail_status"
    DISCONNECT_GMAIL = "/disconnect_gmail"

    @property
    def description(self) -> str:
        descriptions = {
            Cmd.STATUS: "bot status",
            Cmd.HELP: "available commands",
            Cmd.HEALTH: "run health check",
            Cmd.INVOICE: "generate invoice",
            Cmd.ABOUT: "project info",
            Cmd.WHOAMI: "show current Telegram identity",
            Cmd.LAST_ACTION: "show last action",
            Cmd.CONNECT_GMAIL: "connect gmail",
            Cmd.GMAIL_STATUS: "is gmail connected",
            Cmd.DISCONNECT_GMAIL: "disconnect gmail",
        }

        return descriptions[self]


class BotInfo:
    """Текстовые константы Telegram-бота."""

    ABOUT = "🤖 Finpipe MVP\n\nFeatures:\n• Invoice generation\n• Gmail integration\n• Telegram bot\n• SQLite storage\n\nVersion: 0.1"

    HELP_HEADER = "📚 Available commands"

    PROJECT_RUNNING = "🟢 Finpipe is running."
    TG_API_OK = "✅ Telegram API OK."

    GENERATING_INVOICE = "⏳ Generating invoice..."
    INVOICE_SENT = "✅ Invoice sent."

    ACCESS_DENIED = "⛔ Access denied"
    NO_SUCH_COMMAND = "🫥 No such command"

    WHOAMI_PREFIX = "👤 You are"

    NO_AUDIT_LOG_RECORDS = "📝 No audit records found."
    GMAIL_NOT_CONNECTED = "❌ Gmail is not connected."
    GMAIL_CONNECTED = "✅ Gmail connected"
    GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE = "⚠️ Gmail OAuth is temporarily unavailable."


def build_help_message() -> str:
    """Строит help из зарегистрированных команд."""

    lines = [BotInfo.HELP_HEADER, ""]

    for command in Cmd:
        lines.append(f"{command.value} - {command.description}")

    return "\n".join(lines)


def format_whoami(telegram_id: int | None, username: str | None) -> str:
    """Форматирует информацию о текущем пользователе."""

    return f"{BotInfo.WHOAMI_PREFIX}\ntelegram_id: {telegram_id}\nusername: {username or 'unknown'}"


def format_last_action(action: AuditLog) -> str:
    """Форматирует последнюю запись аудитлога."""

    return (
        f"📝 Last action\n\nUser: {action.user_name}\nCommand: {action.command}\nStatus: {action.status}\nTime: {action.created_at:%Y-%m-%d %H:%M:%S}"
    )
