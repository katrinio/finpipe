"""Проверяет наличие нового письма банка и уведомляет пользователей."""

from __future__ import annotations

import logging
from datetime import date

from src.integrations.gmail.auth import get_gmail_service
from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.gmail.search import find_bank_email
from src.integrations.telegram.client import TelegramClient
from src.logging_config import configure_logging
from src.storage.orm import AllowedUser, ProcessedMessage
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)

# Письмо о зачислении приходит между 2 и 6 числом каждого месяца.
_CHECK_DAY_FROM = 2
_CHECK_DAY_TO = 6

# Префикс маркера в ProcessedMessage — не конфликтует с реальными message_id банка.
# Сбрасывается вместе с историей писем через «Сбросить историю писем».
_NOTIFY_PREFIX = "notify"


def _notification_key(telegram_id: int, message_id: str) -> str:
    return f"{_NOTIFY_PREFIX}:{telegram_id}:{message_id}"


def _is_check_period(today: date | None = None) -> bool:
    today = today or date.today()
    return _CHECK_DAY_FROM <= today.day <= _CHECK_DAY_TO


def check_user(telegram_id: int, telegram: TelegramClient) -> bool:
    """Проверяет Gmail одного пользователя и уведомляет если письмо найдено.

    Возвращает True если уведомление отправлено.
    """
    try:
        service = get_gmail_service(telegram_id)
    except GmailOAuthError:
        LOGGER.info("Gmail not connected for Telegram user %s, skipping", telegram_id)
        return False

    bank_email = find_bank_email(service, owner_telegram_id=telegram_id)
    if bank_email is None:
        LOGGER.info("Bank email not found for Telegram user %s", telegram_id)
        return False

    notify_key = _notification_key(telegram_id, bank_email.message_id)
    if ProcessedMessage.is_processed(notify_key):
        LOGGER.info("Already notified Telegram user %s about bank email %s", telegram_id, bank_email.message_id)
        return False

    LOGGER.info("New bank email found for Telegram user %s: %s", telegram_id, bank_email.message_id)
    message = (
        "📬 Письмо от банка получено!\n"
        f"От: {bank_email.sender}\n"
        f"Тема: {bank_email.subject}\n"
        f"Дата: {bank_email.date}\n\n"
        "Нажми «Подтверждение для банка» чтобы обработать."
    )
    telegram.send_message(telegram_id, message)
    ProcessedMessage.mark_as_processed(notify_key)
    return True


def run_check(today: date | None = None) -> int:
    """Проверяет всех пользователей. Возвращает количество отправленных уведомлений."""

    if not _is_check_period(today):
        LOGGER.info(
            "Skipping bank email check: day %s is outside check period (%s–%s)",
            (today or date.today()).day,
            _CHECK_DAY_FROM,
            _CHECK_DAY_TO,
        )
        return 0

    users = AllowedUser.list_all()
    if not users:
        LOGGER.warning("No allowed users found, nothing to check")
        return 0

    telegram = TelegramClient()
    notified = 0
    for user in users:
        try:
            if check_user(user.telegram_id, telegram):
                notified += 1
        except Exception:
            LOGGER.exception("Bank email check failed for Telegram user %s", user.telegram_id)

    return notified


def main() -> int:
    EnvVar.load_dotenv()
    configure_logging()
    try:
        run_check()
    except Exception:
        LOGGER.exception("Bank email check failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
