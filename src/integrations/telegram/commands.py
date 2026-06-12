from enum import StrEnum

from src.integrations.telegram.ui.messages import BotInfo
from src.storage.orm.system.audit_log import AuditLog


class Cmd(StrEnum):
    MENU = "/menu"
    START = "/start"
    ADD_USER = "/add_user"
    REMOVE_USER = "/remove_user"

    @property
    def description(self) -> str:
        descriptions = {
            Cmd.MENU: "menu",
            Cmd.START: "start the Finpipe bot",
            Cmd.ADD_USER: "grant access to a known Telegram user",
            Cmd.REMOVE_USER: "revoke access from a Telegram user",
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

    username_line = f"@{username}" if username else "unknown"
    return f"{BotInfo.WHOAMI_PREFIX}\nTelegram ID: {telegram_id}\nUsername: {username_line}"


def format_last_action(action: AuditLog) -> str:
    """Форматирует последнюю запись аудитлога."""

    return (
        f"📝 Last action\n\nUser: {action.user_name}\nCommand: {action.command}\nStatus: {action.status}\nTime: {action.created_at:%Y-%m-%d %H:%M:%S}"
    )
