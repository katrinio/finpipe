from cryptography.fernet import Fernet

from src.utils.credentials import EnvVar


class TokenCipher:
    _cipher = None

    @classmethod
    def _get_cipher(cls) -> Fernet:
        if cls._cipher is None:
            cls._cipher = Fernet(EnvVar.get_required_env("SIGNATURE_ENCRYPTION_KEY").encode())

        return cls._cipher

    @classmethod
    def encrypt(cls, text: str) -> str:
        encrypted_bytes = cls._get_cipher().encrypt(text.encode())
        return encrypted_bytes.decode()

    @classmethod
    def decrypt(cls, text: str) -> str:
        decrypted_bytes = cls._get_cipher().decrypt(text.encode())
        return decrypted_bytes.decode()
