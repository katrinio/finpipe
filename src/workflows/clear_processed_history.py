from __future__ import annotations

import logging
from collections.abc import Sequence

from src.storage.processed_messages import clear_processed_history

LOGGER = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    clear_processed_history()

    LOGGER.info("Processed History cleared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
