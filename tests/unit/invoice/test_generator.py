from types import SimpleNamespace

from src.services.invoice.invoice_generator import build_osascript_command, build_replacements


def test_build_replacements_wraps_plain_placeholder_names() -> None:
    invoice_details = SimpleNamespace(
        placeholder_aliases={
            "invoice_number": ("invoiceId", "{{invoiceId}}"),
            "date": ("invoiceDate",),
        }
    )
    data = {
        "invoice_number": "2026-05",
        "date": "29.05.2026",
    }

    replacements = build_replacements(data, invoice_details)

    assert replacements == {
        "{{invoiceId}}": "2026-05",
        "{{invoiceDate}}": "29.05.2026",
    }


def test_build_osascript_command_flattens_script_lines() -> None:
    command = build_osascript_command(
        [
            'tell application "Pages"',
            "activate",
            "end tell",
        ]
    )

    assert command == [
        "osascript",
        "-e",
        'tell application "Pages"',
        "-e",
        "activate",
        "-e",
        "end tell",
    ]
