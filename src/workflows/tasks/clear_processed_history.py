"""CLI-шаг для очистки истории уже обработанных писем банка."""

from __future__ import annotations

import logging

from src.logging_config import configure_logging
from src.storage.dependencies import build_storage_dependencies

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Точка входа для очистки локальной истории processed messages."""

    configure_logging()

    try:
        storage = build_storage_dependencies()
        storage.processed_messages.clear_processed_message()
    except Exception:
        LOGGER.exception("Failed to clear processed bank email history")
        return 1

    LOGGER.info("Cleared processed bank email history")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
