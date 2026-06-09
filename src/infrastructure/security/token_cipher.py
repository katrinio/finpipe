from cryptography.fernet import Fernet

from src.utils.credentials import EnvVar


class TokenCipher:
    _cipher = Fernet(EnvVar.get_required_env("SIGNATURE_ENCRYPTION_KEY").encode())

    @classmethod
    def encrypt(cls, text: str) -> str:
        encrypted_bytes = cls._cipher.encrypt(text.encode())
        return encrypted_bytes.decode()

    @classmethod
    def decrypt(cls, text: str) -> str:
        decrypted_bytes = cls._cipher.decrypt(text.encode())
        return decrypted_bytes.decode()
