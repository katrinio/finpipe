from enum import StrEnum

from src.integrations.telegram.messages import CommonMessages


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


def format_whoami(telegram_id: int | None, username: str | None) -> str:
    """Форматирует информацию о текущем пользователе."""

    username_line = f"@{username}" if username else "unknown"
    return f"{CommonMessages.General.WHOAMI_PREFIX}\nTelegram ID: {telegram_id}\nUsername: {username_line}"


def format_chatid(telegram_id: int | None) -> str:
    """Форматирует идентификатор текущего чата."""

    return f"Chat ID: {telegram_id}"
