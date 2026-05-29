import datetime

from faker import Faker

fake = Faker()


class Utils:
    """Класс для вспомогательных методов."""

    @classmethod
    def today(cls) -> datetime.date:
        return datetime.datetime.now(datetime.UTC).date()

    @staticmethod
    def generate_int_string(length: int = 12) -> str:
        return f"1{fake.bothify('#' * (length - 1))}"

    @staticmethod
    def generate_city() -> str:
        return fake.city()

    @staticmethod
    def generate_name() -> str:
        return fake.name()

    @staticmethod
    def generate_random_sentence() -> str:
        return fake.sentence()
