from src.integrations.gmail import GmailAccountService, GmailOAuth, GmailOAuthSettings
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.messages import BotInfo
from src.utils.credentials import EnvVar


class GmailHandlers:
    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def gmail_connect(self, telegram_id: int, username: str | None) -> None:
        if not GmailOAuthSettings.is_callback_enabled():
            self.telegram.send_message(BotInfo.GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE)
            return
        callback_url = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
        authorization_url, _session = GmailOAuth.build_authorization_url(telegram_id, username, callback_url)
        self.telegram.send_message(f"Open this URL:\n{authorization_url}")

    def gmail_status(self, telegram_id: int) -> None:
        status = GmailAccountService.status(telegram_id)
        if not status.is_connected:
            self.telegram.send_message(BotInfo.GMAIL_NOT_CONNECTED)
            return
        self.telegram.send_message(f"{BotInfo.GMAIL_CONNECTED}\n{status.gmail_email or 'unknown'}")

    def gmail_disconnect(self, telegram_id: int) -> None:
        GmailAccountService.disconnect(telegram_id)
        self.telegram.send_message(BotInfo.GMAIL_DISCONNECTED)
