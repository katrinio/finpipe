"""Workflow для ручной проверки отправки тестового письма через Gmail."""

from __future__ import annotations

import logging

from src.integrations.gmail import GmailSender
from src.logging_config import configure_logging
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Читает `TEST_EMAIL`, отправляет тестовое письмо и возвращает код завершения."""

    configure_logging()

    try:
        test_email = EnvVar.get_required_env("TEST_EMAIL")
        sender = GmailSender()
        message_id = sender.send_email(
            to_email=test_email,
            subject="Finpipe test email",
            body="This is a test email sent from Finpipe.",
            attachments=[],
        )
    except Exception:
        LOGGER.exception("Test email workflow failed")
        return 1

    LOGGER.info("Test email Gmail message id: %s", message_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
