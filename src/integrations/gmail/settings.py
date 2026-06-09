"""Gmail integration feature toggles."""

from __future__ import annotations

from src.utils.credentials import EnvVar


class GmailOAuthSettings:
    """Настройки Gmail OAuth."""

    @classmethod
    def is_callback_enabled(cls) -> bool:
        value = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_ENABLED", "false").strip().lower()
        return value not in {"0", "false", "no", "off"}
