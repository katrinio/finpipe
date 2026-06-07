"""CLI-шаг для очистки истории уже обработанных писем банка."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from src.logging_config import configure_logging
from src.storage.processed_messages import clear_processed_history

LOGGER = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа для очистки локальной истории processed messages."""

    configure_logging()

    try:
        clear_processed_history()
    except Exception:
        LOGGER.exception("Failed to clear processed bank email history")
        return 1

    LOGGER.info("Cleared processed bank email history")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
