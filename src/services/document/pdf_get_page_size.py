class PdfGetPageSize:
    @staticmethod
    def get_page_size(page: object) -> tuple[float, float]:
        return float(page.mediabox.width), float(page.mediabox.height)
