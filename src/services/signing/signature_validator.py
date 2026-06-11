"""Валидация пользовательской подписи перед сохранением."""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from src.services.signing.exceptions import (
    InvalidSignatureFormatError,
    InvalidSignatureImageError,
    SignatureTooLargeError,
)


class SignatureValidator:
    """Проверяет подпись перед загрузкой и шифрованием."""

    MAX_SIZE_BYTES = 2 * 1024 * 1024

    @classmethod
    def validate_png(cls, file_name: str) -> None:
        """Разрешает только PNG-файлы."""

        if not file_name.lower().endswith(".png"):
            msg = f"Signature file must be a PNG image: {file_name}"
            raise InvalidSignatureFormatError(msg)

    @classmethod
    def validate_size(cls, file_size: int) -> None:
        """Проверяет, что размер подписи не превышает лимит."""

        if file_size > cls.MAX_SIZE_BYTES:
            msg = f"Signature file is too large: {file_size} bytes"
            raise SignatureTooLargeError(msg)

    @classmethod
    def validate_image(cls, file_bytes: bytes) -> None:
        """Проверяет, что байты можно открыть как изображение."""

        try:
            with Image.open(BytesIO(file_bytes)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            msg = "Signature file is not a valid image"
            raise InvalidSignatureImageError(msg) from exc
