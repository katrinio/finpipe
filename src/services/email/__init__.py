"""Сервис отправки email-сообщений."""

from .email_builder import EmailBuilder, build_email

__all__ = ["EmailBuilder", "build_email"]
