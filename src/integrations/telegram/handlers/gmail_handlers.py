import logging

from src.integrations.gmail import GmailAccountService, GmailOAuth, GmailOAuthSettings
from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.messages import BotInfo
from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


class GmailHandlers:
    """Обрабатывает Telegram-команды Gmail-интеграции."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def gmail_connect(self, telegram_id: int, username: str | None) -> None:
        """Запускает OAuth-подключение Gmail для пользователя."""

        if not GmailOAuthSettings.is_callback_enabled():
            LOGGER.warning("Gmail connect requested while callback flow is disabled for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BotInfo.GMAIL_OAUTH_TEMPORARILY_UNAVAILABLE)
            return
        try:
            callback_url = EnvVar.get_optional_env("GMAIL_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/gmail/callback")
            authorization_url, _session = GmailOAuth.build_authorization_url(telegram_id, username, callback_url)
        except GmailOAuthError:
            LOGGER.exception("Gmail connect failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BotInfo.GMAIL_CONNECT_FAILED)
            return
        LOGGER.info("Gmail connect initiated for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, f"Open this URL:\n{authorization_url}")

    def gmail_status(self, telegram_id: int) -> None:
        """Показывает текущее состояние Gmail-подключения."""

        status = GmailAccountService.status(telegram_id)
        if not status.is_connected:
            LOGGER.info("Gmail status checked: disconnected for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, BotInfo.GMAIL_NOT_CONNECTED)
            return
        LOGGER.info("Gmail status checked: connected for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, f"{BotInfo.GMAIL_CONNECTED}\n{status.gmail_email or 'unknown'}")

    def gmail_disconnect(self, telegram_id: int) -> None:
        """Отключает сохранённый Gmail-аккаунт пользователя."""

        GmailAccountService.disconnect(telegram_id)
        LOGGER.info("Gmail disconnected for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.GMAIL_DISCONNECTED)
