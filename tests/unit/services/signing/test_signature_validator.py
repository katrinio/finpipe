from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from src.services.signing.exceptions import InvalidSignatureFormatError, InvalidSignatureImageError, SignatureTooLargeError
from src.services.signing.signature_validator import SignatureValidator


def test_validate_png_accepts_png_file() -> None:
    SignatureValidator.validate_png("signature.png")


def test_validate_png_rejects_non_png_file() -> None:
    with pytest.raises(InvalidSignatureFormatError, match="Signature file must be a PNG image"):
        SignatureValidator.validate_png("signature.jpg")


def test_validate_size_accepts_one_megabyte() -> None:
    SignatureValidator.validate_size(1024 * 1024)


def test_validate_size_rejects_three_megabytes() -> None:
    with pytest.raises(SignatureTooLargeError, match="Signature file is too large"):
        SignatureValidator.validate_size(3 * 1024 * 1024)


def test_validate_image_accepts_valid_png_bytes() -> None:
    buffer = BytesIO()
    image = Image.new("RGBA", (1, 1), (255, 255, 255, 255))
    image.save(buffer, format="PNG")

    SignatureValidator.validate_image(buffer.getvalue())


def test_validate_image_rejects_invalid_bytes() -> None:
    with pytest.raises(InvalidSignatureImageError, match="Signature file is not a valid image"):
        SignatureValidator.validate_image(b"not-an-image")


def test_validate_png_accepts_project_png_resource() -> None:
    SignatureValidator.validate_png(str(Path("tests/resources/signature.png")))
