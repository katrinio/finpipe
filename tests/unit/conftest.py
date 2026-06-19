from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_storage_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevents unit tests from touching the database during app lifespan."""
    monkeypatch.setattr(
        "src.interfaces.web.app.build_storage_dependencies",
        MagicMock(),
    )


@pytest.fixture(autouse=True)
def _suppress_pages_app(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevents unit tests from opening Pages.app on macOS during PDF conversion."""
    if "document/test_unit_document_docx_to_pdf_converter" in str(request.node.fspath):
        return

    from src.infrastructure.document import DocxToPdfConverter

    def _fake_convert(cls, rendered_docx_path, output_path):  # type: ignore[no-untyped-def]
        output_path.write_bytes(b"%PDF-1.4 fake")

    monkeypatch.setattr(DocxToPdfConverter, "convert", classmethod(_fake_convert))
