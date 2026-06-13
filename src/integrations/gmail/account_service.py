"""Сервис состояния и обновления Gmail-подключения."""

from dataclasses import dataclass
from datetime import datetime

from src.infrastructure.security.token_cipher import TokenCipher
from src.storage.orm import AllowedUser
from src.storage.orm.user.gmail_account import GmailAccount


@dataclass(frozen=True, slots=True)
class GmailAccountStatus:
    """Статус подключения Gmail для пользователя."""

    is_connected: bool
    gmail_email: str | None
    connected_at: datetime | None
    last_error: str | None


class GmailAccountService:
    """Управляет подключением Gmail и его статусом."""

    @classmethod
    def connect(
        cls,
        telegram_id: int,
        email: str,
        refresh_token: str,
    ) -> None:
        """Сохраняет подключение Gmail и шифрует refresh token."""

        # TODO(vps): закрепить SIGNATURE_ENCRYPTION_KEY как постоянный secret и описать процедуру ротации ключа.
        encrypted_token = TokenCipher.encrypt(refresh_token)

        GmailAccount.update_gmail_credentials(
            telegram_id=telegram_id,
            gmail_email=email,
            gmail_refresh_token=encrypted_token,
        )

    @classmethod
    def disconnect(cls, telegram_id: int) -> None:
        """Удаляет сохранённые Gmail-учётные данные пользователя."""

        GmailAccount.clear_gmail_credentials(telegram_id)

    @classmethod
    def status(cls, telegram_id: int) -> GmailAccountStatus:
        """Возвращает текущее состояние Gmail-подключения."""

        return cls._build_status(GmailAccount.get_by_owner(telegram_id))

    @classmethod
    def _get_user_config(cls, telegram_id: int) -> AllowedUser | None:
        return AllowedUser.get_by_telegram_id(telegram_id)

    @classmethod
    def _build_status(cls, user_config: GmailAccount | None) -> GmailAccountStatus:
        """Преобразует ORM-модель в DTO статуса подключения."""

        if user_config is None:
            return GmailAccountStatus(False, None, None, None)
        return GmailAccountStatus(
            is_connected=bool(user_config.gmail_refresh_token),
            gmail_email=user_config.gmail_email,
            connected_at=user_config.gmail_connected_at,
            last_error=user_config.gmail_last_error,
        )
