"""Набор простых утилит для дат, тестовых данных и статусов."""

import datetime
import random
import string

from faker import Faker

fake = Faker() if Faker is not None else None


class Utils:
    """Общие небольшие утилиты, используемые в проекте."""

    @staticmethod
    def today() -> datetime.date:
        """Возвращает текущую дату в UTC."""

        return datetime.datetime.now(datetime.UTC).date()

    @staticmethod
    def generate_int_string(length: int = 12) -> str:
        """Генерирует строку цифр заданной длины для тестовых данных."""

        if fake is not None:
            return f"1{fake.bothify('#' * (length - 1))}"

        digits = "".join(random.choice(string.digits) for _ in range(length - 1))
        return f"1{digits}"

    @staticmethod
    def generate_city() -> str:
        """Генерирует случайный город для тестовых сценариев."""

        return fake.city() if fake is not None else "Test City"

    @staticmethod
    def generate_name() -> str:
        """Генерирует случайное имя для тестовых сценариев."""

        return fake.name() if fake is not None else "Test User"

    @staticmethod
    def generate_random_sentence() -> str:
        """Генерирует случайное предложение для тестовых данных."""

        return fake.sentence() if fake is not None else "Test sentence."

    @staticmethod
    def generate_iban() -> str:
        """Генерирует тестовый IBAN."""

        return fake.iban() if fake is not None else "RS35123456789012345678"

    @staticmethod
    def format_status(value: str) -> str:
        """Преобразует внутренний статус в текст для отчёта."""

        return "SUCCESS" if value == "success" else "FAILURE"

    @staticmethod
    def parse_iso_date(value: str | datetime.date | None) -> datetime.date | None:
        """Преобразует ISO-дату в datetime.date."""

        if value is None:
            return None

        if isinstance(value, datetime.date):
            return value

        return datetime.date.fromisoformat(value)
