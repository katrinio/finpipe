from dataclasses import dataclass

from src.services.document.replacement import Replacement


def test_build_replacements_uses_mapping_field_names() -> None:
    data = {
        "invoice_number": "2026-05",
        "amount": 1_000,
    }

    replacements = Replacement.build_replacements(data)

    assert replacements == {
        "{{invoice_number}}": "2026-05",
        "{{amount}}": "1000",
    }


def test_build_replacements_uses_dataclass_field_names() -> None:
    @dataclass(frozen=True)
    class TemplateData:
        account_number: str
        city: str

    replacements = Replacement.build_replacements(
        TemplateData(
            account_number="190-128270-73",
            city="Beograd",
        )
    )

    assert replacements == {
        "{{account_number}}": "190-128270-73",
        "{{city}}": "Beograd",
    }
