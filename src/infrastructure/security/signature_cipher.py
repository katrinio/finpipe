"""Шифрование и расшифровка файлов подписи."""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

from src.utils.credentials import EnvVar

load_dotenv()


class SignatureCipher:
    _cipher: Fernet | None = None

    @classmethod
    def _get_cipher(cls) -> Fernet:
        if cls._cipher is None:
            try:
                key = EnvVar.get_required_env("SIGNATURE_ENCRYPTION_KEY")
            except Exception as exc:  # pragma: no cover - explicit runtime error path
                msg = "Missing required environment variable: SIGNATURE_ENCRYPTION_KEY"
                raise RuntimeError(msg) from exc

            cls._cipher = Fernet(key.encode())

        return cls._cipher

    @classmethod
    def encrypt_file(cls, source: Path, destination: Path) -> Path:
        encrypted = cls._get_cipher().encrypt(source.read_bytes())
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encrypted)
        return destination

    @classmethod
    def decrypt_bytes(cls, encrypted_file: Path) -> bytes:
        try:
            encrypted = encrypted_file.read_bytes()
            return cls._get_cipher().decrypt(encrypted)
        except InvalidToken as exc:
            msg = f"Encrypted signature file is corrupted or invalid: {encrypted_file}"
            raise RuntimeError(msg) from exc
