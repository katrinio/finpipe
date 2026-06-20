import subprocess
from datetime import UTC, datetime

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.commands import format_chatid, format_recent_errors, format_recent_events, format_stats
from src.integrations.telegram.settings import TelegramSettings
from src.integrations.telegram.ui.messages import CommonMessages
from src.services.monitoring.event_analytics import EventAnalytics
from src.storage.orm.system.telegram_update import TelegramUpdate
from src.storage.orm.user.allowed_user import AllowedUser
from src.utils.credentials import LOGGER, EnvVar


class MonitoringHandler:
    """Обрабатывает текстовые команды мониторингового чата."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    _HELP = (
        "📖 Доступные команды:\n\n"
        "/health — Telegram API, БД, последняя активность\n"
        "/events — последние 10 событий\n"
        "/errors — последние 10 ошибок\n"
        "/stats — статистика событий и документов\n"
        "/logs [N] — последние N строк из контейнера (по умолчанию 50)\n"
        "/chatid — ID этого чата\n"
        "/help — список команд"
    )

    def handle_message(self, text: str | None, chat_id: int | None, telegram_id: int | None, username: str | None) -> bool:
        """Обрабатывает команды мониторингового чата."""

        monitoring_chat_id = TelegramSettings.get_monitoring_chat_id()
        if monitoring_chat_id is None or chat_id != monitoring_chat_id or text is None:
            return False

        try:
            command = self._normalize_command(text)
            if command == "/health":
                self._health(chat_id)
                return True
            if command == "/events":
                self._events(chat_id)
                return True
            if command == "/errors":
                self._errors(chat_id)
                return True
            if command == "/stats":
                self._stats(chat_id)
                return True
            if command == "/chatid":
                self.telegram.send_message(chat_id, format_chatid(chat_id))
                return True
            if command.startswith("/logs"):
                self._logs(chat_id, text)
                return True
            if command == "/help":
                self.telegram.send_message(chat_id, self._HELP)
                return True

            if text.startswith("/"):
                self.telegram.send_message(chat_id, f"❓ Неизвестная команда.\n\n{self._HELP}")
            return True
        except Exception:
            LOGGER.exception("Monitoring command failed in chat %s", chat_id)
            self.telegram.send_message(chat_id, CommonMessages.Errors.SYSTEM_ERROR)
            return True

    def _logs(self, chat_id: int, text: str) -> None:
        parts = text.strip().split()
        try:
            tail = int(parts[1]) if len(parts) > 1 else 50
            tail = max(1, min(tail, 200))
        except ValueError:
            self.telegram.send_message(chat_id, "⚠️ Использование: /logs [N] — последние N строк (макс. 200)")
            return

        container = EnvVar.get_optional_env("CONTAINER_NAME", "finpipe-bot")
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            output = (result.stdout + result.stderr).strip()
        except FileNotFoundError:
            self.telegram.send_message(chat_id, "❌ docker не найден — сокет смонтирован?")
            return
        except subprocess.TimeoutExpired:
            self.telegram.send_message(chat_id, "❌ Таймаут при получении логов")
            return

        if not output:
            self.telegram.send_message(chat_id, "📋 Логи пусты")
            return

        header = f"📋 Последние {tail} строк [{container}]\n\n"
        # Telegram limit: 4096 chars
        body = output[-(4096 - len(header)) :]
        self.telegram.send_message(chat_id, f"{header}{body}")

    def _health(self, chat_id: int) -> None:
        lines = ["🏥 Health"]

        # Telegram API
        try:
            self.telegram.healthcheck()
            lines.append("✅ Telegram API")
        except Exception:
            lines.append("❌ Telegram API")

        # DB — через AllowedUser.count()
        try:
            user_count = AllowedUser.count()
            lines.append(f"✅ База данных  ({user_count} польз.)")
        except Exception:
            lines.append("❌ База данных")

        # Последняя активность бота
        try:
            last_at = TelegramUpdate.get_last_processed_at()
            if last_at is not None:
                lines.append(f"📨 Последняя активность: {last_at.strftime('%Y-%m-%d %H:%M UTC')}")
            else:
                lines.append("📨 Активности ещё не было")
        except Exception:
            lines.append("⚠️ Не удалось получить время последней активности")

        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"\n🕐 {now}")
        self.telegram.send_message(chat_id, "\n".join(lines))

    def _events(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(chat_id, format_recent_events(analytics.get_recent_events(limit=10)))

    def _errors(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(chat_id, format_recent_errors(analytics.get_recent_errors(limit=10)))

    def _stats(self, chat_id: int) -> None:
        analytics = EventAnalytics()
        self.telegram.send_message(
            chat_id,
            format_stats(
                total_events=analytics.get_total_events(),
                event_counts=analytics.get_event_counts(),
                document_stats=analytics.get_document_generation_stats(),
                error_count=analytics.get_error_counts(),
                recent_error_count=len(analytics.get_recent_errors(limit=3)),
            ),
        )

    @staticmethod
    def _normalize_command(text: str) -> str:
        return text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
