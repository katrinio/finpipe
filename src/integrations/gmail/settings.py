"""Feature toggle для Gmail OAuth callback."""

from src.utils.credentials import EnvVar


class GmailOAuthSettings:
    """Настройки Gmail OAuth."""

    @classmethod
    def is_callback_enabled(cls) -> bool:
        value = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_ENABLED", "false").strip().lower()
        return value not in {"0", "false", "no", "off"}

    @classmethod
    def get_callback_url(cls) -> str:
        return EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
