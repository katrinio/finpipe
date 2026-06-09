from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from src.infrastructure.security.signature_cipher import SignatureCipher
from src.utils.credentials import ENV_PATH_OVERRIDE, EnvVar


@pytest.fixture(autouse=True)
def reset_cipher_cache() -> Generator[None]:
    SignatureCipher._cipher = None
    yield
    SignatureCipher._cipher = None


def test_encrypt_then_decrypt_returns_original_bytes(tmp_path: Path) -> None:
    source = tmp_path / "signature.png"
    encrypted = tmp_path / "signature.enc"
    source.write_bytes(b"signature-bytes")

    SignatureCipher.encrypt_file(source, encrypted)

    assert SignatureCipher.decrypt_bytes(encrypted) == b"signature-bytes"


def test_encrypt_file_raises_when_key_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "signature.png"
    encrypted = tmp_path / "signature.enc"
    source.write_bytes(b"signature-bytes")

    monkeypatch.setenv(ENV_PATH_OVERRIDE, str(tmp_path / "missing.env"))
    monkeypatch.delenv("SIGNATURE_ENCRYPTION_KEY", raising=False)
    EnvVar.reset_dotenv_cache()

    with pytest.raises(RuntimeError, match="SIGNATURE_ENCRYPTION_KEY"):
        SignatureCipher.encrypt_file(source, encrypted)


def test_decrypt_bytes_raises_for_corrupted_encrypted_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encrypted = tmp_path / "signature.enc"
    encrypted.write_bytes(b"not-a-fernet-token")

    monkeypatch.setenv("SIGNATURE_ENCRYPTION_KEY", Fernet.generate_key().decode())
    EnvVar.reset_dotenv_cache()

    with pytest.raises(RuntimeError, match="corrupted or invalid"):
        SignatureCipher.decrypt_bytes(encrypted)
