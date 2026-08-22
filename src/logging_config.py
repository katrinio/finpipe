"""Единая настройка логирования для CLI и workflow-скриптов."""

import logging
import os
import sys
from urllib.parse import unquote, urlsplit

DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
SENSITIVE_ENV_NAMES = (
    "DATABASE_URL",
    "TELEGRAM_BOT_TOKEN",
    "SIGNATURE_ENCRYPTION_KEY",
    "BOT_OWNER_TELEGRAM_ID",
)


class SensitiveDataFormatter(logging.Formatter):
    """Redacts configured credentials from messages and exception tracebacks."""

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        for value in self._sensitive_values():
            rendered = rendered.replace(value, "***")
        return rendered

    @staticmethod
    def _sensitive_values() -> tuple[str, ...]:
        values = {value for name in SENSITIVE_ENV_NAMES if (value := os.getenv(name))}
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            password = urlsplit(database_url).password
            if password:
                values.add(password)
                values.add(unquote(password))
        return tuple(sorted(values, key=len, reverse=True))


def configure_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    """Включает базовое логирование с общим форматом сообщений."""

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        stream=sys.stdout,
        force=True,
    )
    formatter = SensitiveDataFormatter(LOG_FORMAT)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)

    # urllib3 logs the complete HTTP path at DEBUG, which includes Telegram's
    # token because Bot API authentication is part of the URL.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
