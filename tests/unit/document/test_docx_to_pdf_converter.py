import logging
from pathlib import Path

import pytest

from src.services.document.docx_to_pdf_converter import DocxToPdfConverter


def test_build_osascript_command_flattens_script_lines() -> None:
    command = DocxToPdfConverter.build_osascript_command(
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


def test_build_pages_export_script_uses_docx_and_pdf_paths() -> None:
    script = DocxToPdfConverter.build_pages_export_script(
        rendered_docx_path=Path("/tmp/invoice.docx"),
        output_path=Path("/tmp/invoice.pdf"),
    )

    assert script == [
        'tell application "Pages"',
        "activate",
        'open POSIX file "/tmp/invoice.docx"',
        "delay 2",
        "set docRef to front document",
        'export docRef to POSIX file "/tmp/invoice.pdf" as PDF',
        "close docRef saving no",
        "end tell",
    ]


def test_convert_runs_pages_steps_with_resolved_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    rendered_docx_path = tmp_path / "invoice.docx"
    output_path = tmp_path / "invoice.pdf"
    rendered_docx_path.write_bytes(b"docx")
    output_path.write_bytes(b"old pdf")

    opened_paths: list[Path] = []
    exported_paths: list[tuple[Path, Path]] = []

    monkeypatch.setattr(
        DocxToPdfConverter,
        "ensure_pages_installed",
        classmethod(lambda cls: None),
    )
    monkeypatch.setattr(
        DocxToPdfConverter,
        "open_with_pages",
        classmethod(lambda cls, path: opened_paths.append(path)),
    )

    def export_pdf(cls: type[DocxToPdfConverter], docx_path: Path, pdf_path: Path) -> None:
        exported_paths.append((docx_path, pdf_path))
        assert not pdf_path.exists()
        pdf_path.write_bytes(b"%PDF")

    monkeypatch.setattr(
        DocxToPdfConverter,
        "export_front_pages_document",
        classmethod(export_pdf),
    )

    caplog.set_level(logging.INFO)

    DocxToPdfConverter.convert(rendered_docx_path, output_path)

    assert opened_paths == [rendered_docx_path.resolve()]
    assert exported_paths == [(rendered_docx_path.resolve(), output_path.resolve())]
    assert output_path.read_bytes() == b"%PDF"
    assert "Starting DOCX to PDF conversion with Pages" in caplog.text
    assert "Finished DOCX to PDF conversion with Pages" in caplog.text


def test_ensure_pages_installed_raises_when_pages_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(DocxToPdfConverter, "PAGES_APP_PATH", tmp_path / "missing.app")

    with pytest.raises(FileNotFoundError, match=r"Pages\.app not found"):
        DocxToPdfConverter.ensure_pages_installed()


def test_validate_output_rejects_missing_and_empty_pdf(tmp_path: Path) -> None:
    missing_pdf = tmp_path / "missing.pdf"
    empty_pdf = tmp_path / "empty.pdf"
    valid_pdf = tmp_path / "valid.pdf"

    with pytest.raises(RuntimeError, match="Pages did not create PDF"):
        DocxToPdfConverter.validate_output(missing_pdf)

    empty_pdf.touch()
    with pytest.raises(RuntimeError, match="Generated PDF is empty"):
        DocxToPdfConverter.validate_output(empty_pdf)

    valid_pdf.write_bytes(b"%PDF")
    DocxToPdfConverter.validate_output(valid_pdf)
