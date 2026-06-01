import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class HistoryStorage:
    FILE_PATH = Path(__file__).with_name("history.json")

    @classmethod
    def load_history(cls) -> set[str]:
        if not cls.FILE_PATH.exists():
            return set()

        with open(cls.FILE_PATH, encoding="utf-8") as file:
            data = json.load(file)

        return set(data.get("invoices", []))

    @classmethod
    def invoice_exists(cls, invoice_number: str) -> bool:
        return invoice_number in cls.load_history()

    @classmethod
    def add_invoice(cls, invoice_number: str) -> None:
        invoices = cls.load_history()
        invoices.add(invoice_number)

        with open(cls.FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(
                {"invoices": sorted(invoices)},
                file,
                indent=4,
                ensure_ascii=False,
            )

        LOGGER.info("Saved invoice %s", invoice_number)

    @classmethod
    def list_invoices(cls) -> list[str]:
        return sorted(cls.load_history())

    @classmethod
    def get_last_invoice(cls) -> str | None:
        invoices = sorted(cls.load_history())

        if not invoices:
            return None

        return invoices[-1]
