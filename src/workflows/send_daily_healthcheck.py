import os

from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.utils.credentials import LOGGER


def main() -> int:
    configure_logging()

    try:
        TelegramClient().send_daily_report(
            unit_status=os.environ["UNIT_STATUS"],
            integration_status=os.environ["INTEGRATION_STATUS"],
            telegram_status=os.environ["TELEGRAM_STATUS"],
            duration_seconds=int(os.environ["DURATION"]),
        )
    except Exception:
        LOGGER.exception("Healthcheck failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
