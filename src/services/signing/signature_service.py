"""Загрузка пользовательской подписи в encrypted storage и БД."""

import hashlib
import logging
import tempfile
from pathlib import Path

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.services.signing.signature_validator import SignatureValidator
from src.storage.orm import Signature
from src.utils.files import delete_file

LOGGER = logging.getLogger(__name__)


class SignatureService:
    """Сервис загрузки пользовательской подписи."""

    @classmethod
    def upload(
        cls,
        telegram_id: int,
        file_name: str,
        file_size: int,
        file_bytes: bytes,
    ) -> None:
        """Валидирует, шифрует и сохраняет подпись пользователя."""

        SignatureValidator.validate_png(file_name)
        SignatureValidator.validate_size(file_size)
        SignatureValidator.validate_image(file_bytes)

        temp_path = cls._save_temp_png(file_bytes)
        destination = cls._build_destination(telegram_id)
        success = False

        try:
            encrypted_path = SignatureCipher.encrypt_file(temp_path, destination)
            encrypted_bytes = encrypted_path.read_bytes()
            signature_hash = hashlib.sha256(encrypted_bytes).hexdigest()
            Signature.create(
                owner_telegram_id=telegram_id,
                signature_path=encrypted_path,
                signature_hash=signature_hash,
                signature_data=encrypted_bytes,
                active=True,
            )
            success = True
        finally:
            delete_file(temp_path, LOGGER)
            if not success:
                delete_file(destination, LOGGER)

    @staticmethod
    def _build_destination(telegram_id: int) -> Path:
        return Dir.STORAGE_DIR / "signatures" / f"{telegram_id}_sign.enc"

    @staticmethod
    def _save_temp_png(file_bytes: bytes) -> Path:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            return Path(tmp_file.name)
