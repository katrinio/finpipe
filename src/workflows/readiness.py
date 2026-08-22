"""Readiness check for the production Telegram polling container."""

import logging

from sqlalchemy import select

from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.storage.orm import BankDetails, CompanyProfile, Signature, TelegramUpdate, UserConfig, UserStateStorage
from src.storage.orm.database import Database

LOGGER = logging.getLogger(__name__)


def check_readiness() -> None:
    """Verifies Telegram access and compatibility of the active ORM schema."""

    database = Database.from_env()
    database.bind_models()
    with database.session() as session:
        for model in (BankDetails, CompanyProfile, Signature, TelegramUpdate, UserConfig, UserStateStorage):
            session.execute(select(model).limit(1)).first()
    TelegramClient().healthcheck()


def main() -> int:
    configure_logging()
    try:
        check_readiness()
    except Exception as error:
        LOGGER.error("Finpipe readiness check failed: %s", type(error).__name__)
        return 1
    LOGGER.info("Finpipe readiness check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
