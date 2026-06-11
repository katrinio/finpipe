"""HTTP callback entrypoint for Gmail OAuth."""

from src.integrations.gmail.oauth_callback import GmailOAuthCallbackService
from src.integrations.gmail.settings import GmailOAuthSettings
from src.utils.credentials import EnvVar


def gmail_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> str:
    if not GmailOAuthSettings.is_callback_enabled():
        return "Gmail OAuth callback is temporarily unavailable"
    callback_url = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
    result = GmailOAuthCallbackService.handle_callback(code=code, state=state, error=error, callback_url=callback_url)
    return result.message
