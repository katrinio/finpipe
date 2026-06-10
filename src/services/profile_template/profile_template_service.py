"""Загрузка пользовательской подписи в encrypted storage и БД."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from src.constants import Dir
from src.infrastructure.security.signature_cipher import SignatureCipher
from src.services.signing.signature_validator import SignatureValidator
from src.storage.orm import Signature


class ProfileTemplateService:
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

        temp_path = cls._save_temp_profile_template(file_bytes)
        destination = cls._build_destination(telegram_id)

        try:
            encrypted_path = SignatureCipher.encrypt_file(temp_path, destination)
            signature_hash = hashlib.sha256(encrypted_path.read_bytes()).hexdigest()
            Signature.create(
                owner_telegram_id=telegram_id,
                signature_path=encrypted_path,
                signature_hash=signature_hash,
                active=True,
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _build_destination(telegram_id: int) -> Path:
        return Dir.STORAGE_DIR / "signatures" / f"{telegram_id}_sign.enc"

    @staticmethod
    def _save_temp_profile_template(file_bytes: bytes) -> Path:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            return Path(tmp_file.name)
