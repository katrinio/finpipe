"""Feature toggle для Gmail OAuth callback."""

import logging

from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


class GmailOAuthSettings:
    """Настройки Gmail OAuth."""

    @classmethod
    def is_callback_enabled(cls) -> bool:
        value = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_ENABLED", "false").strip().lower()
        return value not in {"0", "false", "no", "off"}

    @classmethod
    def get_callback_url(cls) -> str:
        callback_url = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
        LOGGER.info("OAuth callback URL loaded")
        return callback_url
