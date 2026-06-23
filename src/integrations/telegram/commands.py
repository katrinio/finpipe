from enum import StrEnum

from src.integrations.telegram.messages import CommonMessages
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

    lines = [CommonMessages.General.HELP_HEADER, ""]

    for command in Cmd:
        lines.append(f"{command.value} - {command.description}")

    return "\n".join(lines)


def format_whoami(telegram_id: int | None, username: str | None) -> str:
    """Форматирует информацию о текущем пользователе."""

    username_line = f"@{username}" if username else "unknown"
    return f"{CommonMessages.General.WHOAMI_PREFIX}\nTelegram ID: {telegram_id}\nUsername: {username_line}"


def format_chatid(telegram_id: int | None) -> str:
    """Форматирует идентификатор текущего чата."""

    return f"Chat ID: {telegram_id}"


def format_last_action(action: AuditLog) -> str:
    """Форматирует последнюю запись аудитлога."""

    return (
        f"📝 Last action\n\nUser: {action.user_name}\nCommand: {action.command}\nStatus: {action.status}\nTime: {action.created_at:%Y-%m-%d %H:%M:%S}"
    )


def format_recent_errors(errors: list[dict[str, object]]) -> str:
    if not errors:
        return "🚨 Recent Errors\n\n• no data"

    blocks = ["🚨 Recent Errors"]
    for error in errors:
        created_at = error["created_at"]
        created = created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, "strftime") else str(created_at)
        details = error.get("details")
        category = error_type = error_message = None
        if isinstance(details, dict):
            category = details.get("category")
            error_type = details.get("error_type")
            error_message = details.get("error_message")
        block = "\n".join(
            [
                "─" * 20,
                f"🕐 {created}",
                f"📂 {category or 'uncategorized'}  •  {error_type or 'UnknownError'}",
            ]
        )
        if error_message:
            block += f"\n💬 {error_message}"
        blocks.append(block)

    return "\n".join(blocks)
