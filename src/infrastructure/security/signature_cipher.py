from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import load_dotenv

from src.utils.credentials import EnvVar

load_dotenv()


class SignatureCipher:
    _cipher = Fernet(EnvVar.get_required_env("SIGNATURE_ENCRYPTION_KEY").encode())

    @classmethod
    def encrypt_file(cls, source: Path, destination: Path) -> None:
        encrypted = cls._cipher.encrypt(source.read_bytes())
        destination.write_bytes(encrypted)

    @classmethod
    def decrypt_bytes(cls, encrypted_file: Path) -> bytes:
        encrypted = encrypted_file.read_bytes()
        return cls._cipher.decrypt(encrypted)
