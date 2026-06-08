from enum import StrEnum


class Cmd(StrEnum):
    STATUS = "/status"
    HELP = "/help"
    HEALTH = "/health"
    INVOICE = "/invoice"
    ABOUT = "/about"
    WHOAMI = "/whoami"
    LAST_ACTION = "/last_action"

    @property
    def description(self) -> str:
        return {
            Cmd.STATUS: "bot status",
            Cmd.HELP: "available commands",
            Cmd.HEALTH: "run health check",
            Cmd.INVOICE: "generate invoice",
            Cmd.ABOUT: "bot about",
            Cmd.WHOAMI: "show current Telegram identity",
            Cmd.LAST_ACTION: "last action",
        }[self]


class BotInfo:
    ABOUT = "🤖 Finpipe MVP\n\nFeatures:\n• Invoice generation\n• Gmail integration\n• Telegram bot\n• SQLite storage\n\nVersion: 0.1"
    HELP_HEADER = "📚 Available commands."
    PROJECT_RUNNING = "🟢 Finpipe is running."
    TG_API_OK = "✅ Telegram API OK."
    GENERATING_INVOICE = "⏳ Generating invoice..."
    INVOICE_SENT = "✅ Invoice sent."
    NO_SUCH_COMMAND = "🫥 No such command."
    WHOAMI_PREFIX = "👤 You are"
    ACCESS_DENIED = "⛔ Access denied"
    NO_AUDIT_LOG_RECORDS = "No audit records found"


def build_help_message() -> str:
    lines = [BotInfo.HELP_HEADER, ""]

    for cmd in Cmd:
        lines.append(f"{cmd.value} - {cmd.description}")

    return "\n".join(lines)
