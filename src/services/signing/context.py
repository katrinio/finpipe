"""Координаты размещения подписи в PDF-документах."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfSignaturePosition:
    """Координаты и размер блока подписи на странице PDF."""

    x: int
    y: int
    height: int


class SignaturePositions:
    """Набор позиций подписи для поддерживаемых документов."""

    BANK = PdfSignaturePosition(
        x=420,
        y=100,
        height=70,
    )

    CONVERSION_ORDER = PdfSignaturePosition(
        x=400,
        y=450,
        height=80,
    )
