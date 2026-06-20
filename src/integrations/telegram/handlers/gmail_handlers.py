import logging

from src.integrations.gmail.account_service import GmailAccountService
from src.integrations.gmail.exceptions import GmailOAuthError
from src.integrations.gmail.gmail_oauth import GmailOAuth
from src.integrations.gmail.settings import GmailOAuthSettings
from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.ui.buttons import GmailButtons, NavigationButtons
from src.integrations.telegram.ui.menu.integration_menu import build_gmail_clear_history_confirm_menu, build_gmail_menu
from src.integrations.telegram.ui.messages import GmailMessages
from src.storage.orm.system.processed_message import ProcessedMessage

LOGGER = logging.getLogger(__name__)


class GmailHandlers:
    """Обрабатывает Telegram-команды Gmail-интеграции."""

    def __init__(self, telegram: TelegramClient) -> None:
        self.telegram = telegram

    def gmail_connect(self, telegram_id: int, username: str | None) -> None:
        """Запускает OAuth-подключение Gmail для пользователя."""

        if not GmailOAuthSettings.is_callback_enabled():
            LOGGER.warning("Gmail connect requested while callback flow is disabled for Telegram user %s", telegram_id)
            self.telegram.send_message(
                telegram_id,
                GmailMessages.Validation.OAUTH_TEMPORARILY_UNAVAILABLE,
                reply_markup=build_gmail_menu(),
            )
            return
        try:
            callback_url = GmailOAuthSettings.get_callback_url()
            authorization_url, _session = GmailOAuth.build_authorization_url(telegram_id, username, callback_url)
        except GmailOAuthError:
            LOGGER.exception("Gmail connect failed for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, GmailMessages.Connect.FAILED, reply_markup=build_gmail_menu())
            return
        LOGGER.info("OAuth started for Telegram user %s", telegram_id)
        self.telegram.send_message(
            telegram_id,
            GmailMessages.Connect.CONNECT_PROMPT,
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": GmailButtons.GMAIL_CONNECT_INLINE,
                            "url": authorization_url,
                        },
                        {
                            "text": NavigationButtons.HOME,
                            "callback_data": NavigationButtons.HOME,
                        },
                    ]
                ]
            },
        )

    def gmail_status(self, telegram_id: int) -> None:
        """Показывает текущее состояние Gmail-подключения."""

        status = GmailAccountService.status(telegram_id)
        if not status.is_connected:
            LOGGER.info("Gmail status checked: disconnected for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, GmailMessages.Status.NOT_CONNECTED, reply_markup=build_gmail_menu())
            return
        LOGGER.info("Gmail status checked: connected for Telegram user %s", telegram_id)
        text = f"{GmailMessages.Status.CONNECTED}\n{status.gmail_email or 'unknown'}"
        if status.last_error:
            text += f"\n\n⚠️ Последняя ошибка: {status.last_error}"
        self.telegram.send_message(telegram_id, text, reply_markup=build_gmail_menu())

    def gmail_disconnect(self, telegram_id: int) -> None:
        """Отключает сохранённый Gmail-аккаунт пользователя."""

        GmailAccountService.disconnect(telegram_id)
        LOGGER.info("Gmail disconnected for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, GmailMessages.Connect.DISCONNECTED, reply_markup=build_gmail_menu())

    def gmail_clear_history(self, telegram_id: int) -> None:
        """Показывает промпт подтверждения перед сбросом истории."""

        self.telegram.send_message(
            telegram_id,
            GmailMessages.History.CLEAR_PROMPT,
            reply_markup=build_gmail_clear_history_confirm_menu(),
        )

    def gmail_clear_history_confirm(self, telegram_id: int) -> None:
        """Сбрасывает историю обработанных писем банка после подтверждения."""

        ProcessedMessage.clear_processed_message()
        LOGGER.info("Processed bank email history cleared by Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, GmailMessages.History.CLEARED, reply_markup=build_gmail_menu())
