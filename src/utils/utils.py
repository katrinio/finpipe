"""Набор простых утилит для дат, тестовых данных и статусов."""

import datetime
import secrets
import string


class Utils:
    """Общие небольшие утилиты, используемые в проекте."""

    @staticmethod
    def today() -> datetime.date:
        """Возвращает текущую дату в UTC."""

        return datetime.datetime.now(datetime.UTC).date()

    @staticmethod
    def generate_int_string(length: int = 12) -> str:
        """Генерирует строку цифр заданной длины для тестовых данных."""

        digits = "".join(secrets.choice(string.digits) for _ in range(length - 1))
        return f"1{digits}"

    @staticmethod
    def generate_city() -> str:
        """Генерирует случайный город для тестовых сценариев."""

        return "Test City"

    @staticmethod
    def generate_name() -> str:
        """Генерирует случайное имя для тестовых сценариев."""

        return "Test User"

    @staticmethod
    def generate_random_sentence() -> str:
        """Генерирует случайное предложение для тестовых данных."""

        return "Test sentence."

    @staticmethod
    def parse_iso_date(value: str | datetime.date | None) -> datetime.date | None:
        """Преобразует ISO-дату в datetime.date."""

        if value is None:
            return None

        if isinstance(value, datetime.date):
            return value

        return datetime.date.fromisoformat(value)
