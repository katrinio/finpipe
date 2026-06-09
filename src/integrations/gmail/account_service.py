from src.infrastructure.security.token_cipher import TokenCipher
from src.storage.orm.user_config import UserConfig


class GmailAccountService:
    @classmethod
    def connect(cls, telegram_id: int, email: str, authorization_code: str) -> None:
        encrypted_token = TokenCipher.encrypt(authorization_code)
        UserConfig.update_gmail_credentials(
            telegram_id=telegram_id,
            email=email,
            refresh_token=encrypted_token,
        )
