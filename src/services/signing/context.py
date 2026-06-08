"""Координаты подписей гп PDF-доках."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfSignaturePosition:
    x: int
    y: int
    height: int


class SignaturePositions:
    BANK = PdfSignaturePosition(
        x=370,
        y=120,
        height=40,
    )

    TRANSFER_REQUEST = PdfSignaturePosition(
        x=350,
        y=180,
        height=40,
    )
