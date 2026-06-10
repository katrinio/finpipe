"""Services for Gmail account connection status and storage updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.infrastructure.security.token_cipher import TokenCipher
from src.storage.orm.gmail_account import GmailAccount
from src.storage.orm.user_config import UserConfig


@dataclass(frozen=True, slots=True)
class GmailAccountStatus:
    is_connected: bool
    gmail_email: str | None
    connected_at: datetime | None
    last_error: str | None


class GmailAccountService:
    @classmethod
    def connect(
        cls,
        telegram_id: int,
        email: str,
        refresh_token: str,
    ) -> None:
        encrypted_token = TokenCipher.encrypt(refresh_token)

        GmailAccount.update_gmail_credentials(
            telegram_id=telegram_id,
            gmail_email=email,
            gmail_refresh_token=encrypted_token,
        )

    @classmethod
    def disconnect(cls, telegram_id: int) -> None:
        GmailAccount.clear_gmail_credentials(telegram_id)

    @classmethod
    def status(cls, telegram_id: int) -> GmailAccountStatus:
        return cls._build_status(GmailAccount.get_by_owner(telegram_id))

    @classmethod
    def _get_user_config(cls, telegram_id: int) -> UserConfig | None:
        return UserConfig.get_by_telegram_id(telegram_id)

    @classmethod
    def _build_status(cls, user_config: GmailAccount | None) -> GmailAccountStatus:
        if user_config is None:
            return GmailAccountStatus(False, None, None, None)
        return GmailAccountStatus(
            is_connected=bool(user_config.gmail_refresh_token),
            gmail_email=user_config.gmail_email,
            connected_at=user_config.gmail_connected_at,
            last_error=user_config.gmail_last_error,
        )
