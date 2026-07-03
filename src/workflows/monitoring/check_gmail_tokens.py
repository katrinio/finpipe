"""Проверка валидности Gmail OAuth токенов всех подключённых пользователей."""

import logging

from src.integrations.gmail.auth import load_connected_account_credentials
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.storage.dependencies import build_storage_dependencies
from src.storage.orm.user.gmail_account import GmailAccount

LOGGER = logging.getLogger(__name__)

RECONNECT_PROMPT = "⚠️ Gmail отключился — токен истёк или был отозван.\nПожалуйста, переподключите Gmail в разделе «Gmail»."


def check_gmail_tokens(telegram: TelegramClient) -> None:
    """Проверяет refresh token каждого подключённого пользователя и уведомляет при сбое."""

    accounts = GmailAccount.get_all_connected()
    LOGGER.info("Gmail token check: %s connected accounts", len(accounts))

    for account in accounts:
        telegram_id = account.owner_telegram_id
        credentials = load_connected_account_credentials(telegram_id)
        if credentials is None:
            LOGGER.warning("Gmail token expired for Telegram user %s — notifying", telegram_id)
            telegram.send_message(telegram_id, RECONNECT_PROMPT)
        else:
            LOGGER.info("Gmail token OK for Telegram user %s", telegram_id)


def main() -> int:
    configure_logging()
    build_storage_dependencies()
    telegram = TelegramClient()
    try:
        check_gmail_tokens(telegram)
    except Exception:
        LOGGER.exception("Gmail token check failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
