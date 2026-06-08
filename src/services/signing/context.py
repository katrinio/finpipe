"""Координаты подписей гп PDF-доках."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfSignaturePosition:
    x: int
    y: int
    height: int


class SignaturePositions:
    BANK = PdfSignaturePosition(
        x=420,
        y=100,
        height=70,
    )

    TRANSFER_REQUEST = PdfSignaturePosition(
        x=350,
        y=180,
        height=40,
    )
