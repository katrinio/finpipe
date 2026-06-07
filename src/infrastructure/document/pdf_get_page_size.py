"""Извлечение размеров страницы PDF в формате для reportlab."""

from typing import Protocol


class PdfMediaBox(Protocol):
    """Минимальный интерфейс mediabox, нужный генератору."""

    width: float
    height: float


class PdfPage(Protocol):
    """Минимальный интерфейс страницы PDF для чтения размеров."""

    mediabox: PdfMediaBox


class PdfGetPageSize:
    """Адаптер между pypdf и reportlab по размерам страницы."""

    @staticmethod
    def get_page_size(page: PdfPage) -> tuple[float, float]:
        """Возвращает ширину и высоту страницы как числа float."""

        return float(page.mediabox.width), float(page.mediabox.height)
