# Integration-specific fixtures go here.
# Database setup and cleanup is handled by tests/conftest.py.

import pytest

from src.infrastructure.document import docx_to_pdf_converter as converter_module


@pytest.fixture(autouse=True)
def _force_libreoffice_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent Pages from opening windows during integration tests.

    Integration tests run with LibreOffice (headless). If LibreOffice is not
    installed locally, tests that require actual PDF conversion are skipped
    via the existing has_available_converter() skipif guard.
    """
    monkeypatch.setattr(converter_module.sys, "platform", "linux")
