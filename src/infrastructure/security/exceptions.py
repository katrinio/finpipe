"""Исключения инфраструктуры шифрования."""


class SignatureEncryptionError(RuntimeError):
    """Не удалось зашифровать подпись."""


class SignatureDecryptionError(RuntimeError):
    """Не удалось расшифровать подпись."""
