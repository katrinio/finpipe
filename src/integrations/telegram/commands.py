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


def format_stats(
    total_events: int,
    event_counts: dict[str, int],
    document_stats: list[dict[str, object]],
    error_count: int,
    recent_error_count: int,
) -> str:
    lines = [
        "📊 Finpipe Stats",
        "",
        "Events:",
        f"• Total: {total_events}",
        "• Top Events:",
    ]

    for event_type, count in _top_items(event_counts, limit=5):
        lines.append(f"  - {event_type}: {count}")

    lines.extend(
        [
            "",
            "Documents:",
        ]
    )
    if document_stats:
        for item in document_stats[:5]:
            lines.append(f"• {item['document_type']}: {item['count']}")
    else:
        lines.append("• no data")

    lines.extend(
        [
            "",
            "Errors:",
            f"• Last errors: {recent_error_count}",
            f"• Total: {error_count}",
        ]
    )
    return "\n".join(lines)


def format_recent_errors(errors: list[dict[str, object]]) -> str:
    lines = ["🚨 Recent Errors", ""]
    if not errors:
        return "🚨 Recent Errors\n\n• no data"

    for error in errors:
        created_at = error["created_at"]
        created = created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, "strftime") else str(created_at)
        details = error.get("details")
        category = None
        error_type = None
        if isinstance(details, dict):
            category = details.get("category")
            error_type = details.get("error_type")
        lines.append(created)
        lines.append(str(category or "uncategorized"))
        lines.append(str(error_type or "UnknownError"))
        lines.append("")

    return "\n".join(lines).rstrip()


def _top_items(mapping: dict[str, int], limit: int) -> list[tuple[str, int]]:
    return sorted(mapping.items(), key=lambda item: item[1], reverse=True)[:limit]
