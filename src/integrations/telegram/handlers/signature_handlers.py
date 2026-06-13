import logging

from src.integrations.telegram.client import TelegramClient
from src.integrations.telegram.state_service import UserStateService
from src.integrations.telegram.states import UserState
from src.integrations.telegram.ui.menu.profile_menu import build_signature_menu
from src.integrations.telegram.ui.messages import SignatureMessagesV2
from src.services.signing.exceptions import InvalidSignatureFormatError, InvalidSignatureImageError, SignatureTooLargeError
from src.services.signing.signature_service import SignatureService
from src.storage.orm import Signature

LOGGER = logging.getLogger(__name__)


class SignatureHandlers:
    """Обрабатывает загрузку, удаление и статус подписи."""

    def __init__(self, telegram: TelegramClient, state_service: UserStateService) -> None:
        self.telegram = telegram
        self.state_service = state_service

    def upload_signature(self, telegram_id: int) -> None:
        """Переводит пользователя в режим загрузки подписи."""

        LOGGER.info("Signature upload requested by Telegram user %s", telegram_id)
        self.state_service.set_state(telegram_id, UserState.WAITING_SIGNATURE_UPLOAD)
        self.telegram.send_message(telegram_id, SignatureMessagesV2.Upload.REQUIREMENTS, reply_markup=build_signature_menu())

    def handle_signature_upload(self, telegram_id: int, file_name: str, file_size: int, file_bytes: bytes) -> None:
        """Проверяет и сохраняет загруженную подпись пользователя."""

        LOGGER.info("Signature upload started for Telegram user %s", telegram_id)
        try:
            SignatureService.upload(
                telegram_id=telegram_id,
                file_name=file_name,
                file_size=file_size,
                file_bytes=file_bytes,
            )
        except InvalidSignatureFormatError:
            LOGGER.warning("Signature rejected by format for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, SignatureMessagesV2.Validation.NOT_PNG, reply_markup=build_signature_menu())
            return
        except SignatureTooLargeError:
            LOGGER.warning("Signature rejected by size for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, SignatureMessagesV2.Validation.TOO_LARGE, reply_markup=build_signature_menu())
            return
        except InvalidSignatureImageError:
            LOGGER.warning("Signature rejected by content for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, SignatureMessagesV2.Validation.UPLOAD_ERROR, reply_markup=build_signature_menu())
            return

        self.state_service.clear_state(telegram_id)
        LOGGER.info("Signature uploaded for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, SignatureMessagesV2.Upload.UPDATED, reply_markup=build_signature_menu())

    def delete_signature(self, telegram_id: int) -> None:
        """Удаляет текущую подпись пользователя."""

        signature = Signature.get_active(telegram_id)
        if signature is None:
            LOGGER.warning("Signature delete requested but not found for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, SignatureMessagesV2.Status.NOT_FOUND, reply_markup=build_signature_menu())
            return

        Signature.delete(telegram_id)
        LOGGER.info("Signature deleted for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, SignatureMessagesV2.Delete.DELETED, reply_markup=build_signature_menu())

    def signature_status(self, telegram_id: int) -> None:
        """Сообщает, загружена ли подпись для пользователя."""

        if not Signature.is_usable(telegram_id):
            LOGGER.info("Signature status checked: not usable for Telegram user %s", telegram_id)
            self.telegram.send_message(telegram_id, SignatureMessagesV2.Status.NOT_FOUND, reply_markup=build_signature_menu())
            return

        LOGGER.info("Signature status checked: usable for Telegram user %s", telegram_id)
        self.telegram.send_message(telegram_id, SignatureMessagesV2.Status.FOUND, reply_markup=build_signature_menu())
