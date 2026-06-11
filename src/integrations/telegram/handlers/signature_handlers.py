from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.messages import BotInfo
from src.services.signing.exceptions import InvalidSignatureFormatError, InvalidSignatureImageError, SignatureTooLargeError
from src.services.signing.signature_service import SignatureService
from src.storage.orm import Signature


class SignatureHandlers:
    def __init__(self, telegram: TelegramClient, state_service: UserStateService) -> None:
        self.telegram = telegram
        self.state_service = state_service

    def upload_signature(self, telegram_id: int) -> None:
        self.state_service.set_state(telegram_id, UserState.WAITING_SIGNATURE_UPLOAD)
        self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_REQUIREMENTS)

    def handle_signature_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        try:
            SignatureService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidSignatureFormatError:
            self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_NOT_PNG)
            return
        except SignatureTooLargeError:
            self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_TOO_LARGE)
            return
        except InvalidSignatureImageError:
            self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_UPLOAD_ERROR)
            return

        self.state_service.clear_state(telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_UPDATED)

    def delete_signature(self, telegram_id: int) -> None:
        signature = Signature.get_active(telegram_id)
        if signature is None:
            self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_NOT_FOUND)
            return

        Signature.delete(telegram_id)
        self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_DELETED)

    def signature_status(self, telegram_id: int) -> None:
        if not Signature.exists(telegram_id):
            self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_NOT_FOUND)
            return

        self.telegram.send_message(telegram_id, BotInfo.SIGNATURE_FOUND)
