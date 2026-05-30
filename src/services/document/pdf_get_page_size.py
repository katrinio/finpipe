from typing import Protocol


class PdfMediaBox(Protocol):
    width: float
    height: float


class PdfPage(Protocol):
    mediabox: PdfMediaBox


class PdfGetPageSize:
    @staticmethod
    def get_page_size(page: PdfPage) -> tuple[float, float]:
        return float(page.mediabox.width), float(page.mediabox.height)
