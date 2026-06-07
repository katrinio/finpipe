"""Совместимый фасад отправки Gmail-писем."""

from src.integrations.gmail.gmail_sender import DRY_RUN_FAKE_MESSAGE_ID, GmailSender, send_email

__all__ = ["DRY_RUN_FAKE_MESSAGE_ID", "GmailSender", "send_email"]
