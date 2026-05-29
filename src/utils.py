import datetime


class Utils:
    """Класс для вспомогательных методов."""

    @classmethod
    def today(cls) -> datetime.date:
        return datetime.datetime.now(datetime.UTC).date()
