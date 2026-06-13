"""Workflow отправки ежедневного healthcheck-отчёта в Telegram."""

import os

from scripts.bootstrap_allowed_users import bootstrap_primary_admin
from src.constants import Dir
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm import AllowedUser
from src.utils.credentials import LOGGER


def main() -> int:
    """Собирает статусы из окружения и отправляет сводный отчёт."""

    configure_logging()

    try:
        build_storage_dependencies(Dir.STORAGE_DB)
        bootstrap_primary_admin(Dir.STORAGE_DB)
        owner = AllowedUser.get_owner()
        if owner is None:
            raise RuntimeError("Owner is not bootstrapped in storage")
        TelegramClient().send_daily_report(
            owner.telegram_id,
            unit_status=os.environ["UNIT_STATUS"],
            integration_status=os.environ["INTEGRATION_STATUS"],
            telegram_status=os.environ["TELEGRAM_STATUS"],
            duration_seconds=int(os.environ["DURATION"]),
        )
    except Exception:
        LOGGER.exception("Healthcheck failed.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
