"""Набор простых утилит для дат, тестовых данных и статусов."""

import datetime

import arrow
from faker import Faker

fake = Faker()


class Utils:
    """Общие небольшие утилиты, используемые в проекте."""

    @classmethod
    def today(cls) -> datetime.date:
        """Возвращает текущую дату в UTC."""

        return datetime.datetime.now(datetime.UTC).date()

    @staticmethod
    def generate_int_string(length: int = 12) -> str:
        """Генерирует строку цифр заданной длины для тестовых данных."""

        return f"1{fake.bothify('#' * (length - 1))}"

    @staticmethod
    def generate_city() -> str:
        """Генерирует случайный город для тестовых сценариев."""

        return fake.city()

    @staticmethod
    def generate_name() -> str:
        """Генерирует случайное имя для тестовых сценариев."""

        return fake.name()

    @staticmethod
    def generate_random_sentence() -> str:
        """Генерирует случайное предложение для тестовых данных."""

        return fake.sentence()

    @staticmethod
    def generate_iban():
        """Генерирует тестовый IBAN."""

        return fake.iban()

    @classmethod
    def now(cls) -> arrow.Arrow:
        """Возвращает текущее время в формате `arrow`."""

        return arrow.now()

    @classmethod
    def format_status(cls, value: str) -> str:
        """Преобразует внутренний статус в текст для отчёта."""

        return "SUCCESS" if value == "success" else "FAILURE"
