from __future__ import annotations

from enum import StrEnum

from src.integrations.telegram.messages import BotInfo
from src.storage.orm.audit_log import AuditLog


class Cmd(StrEnum):
    MENU = "menu"
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
    UPLOAD_SIGNATURE = "/upload_signature"
    DELETE_SIGNATURE = "/delete_signature"
    SIGNATURE_STATUS = "/signature_status"

    @property
    def description(self) -> str:
        descriptions = {
            Cmd.MENU: "menu",
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
            Cmd.UPLOAD_SIGNATURE: "upload signature",
            Cmd.DELETE_SIGNATURE: "delete signature",
            Cmd.SIGNATURE_STATUS: "show signature status",
        }

        return descriptions[self]


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
