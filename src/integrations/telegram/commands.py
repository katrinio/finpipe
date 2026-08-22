from enum import StrEnum

from src.integrations.telegram.messages import CommonMessages


class Cmd(StrEnum):
    MENU = "/menu"
    START = "/start"


def format_whoami(telegram_id: int | None, username: str | None) -> str:
    """Форматирует информацию о текущем пользователе."""

    username_line = f"@{username}" if username else "unknown"
    return f"{CommonMessages.General.WHOAMI_PREFIX}\nTelegram ID: {telegram_id}\nUsername: {username_line}"


def format_chatid(telegram_id: int | None) -> str:
    """Форматирует идентификатор текущего чата."""

    return f"Chat ID: {telegram_id}"
