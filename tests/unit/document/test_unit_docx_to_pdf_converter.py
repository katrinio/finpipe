import logging
from pathlib import Path

import pytest

from src.infrastructure.document import DocxToPdfConverter
from src.infrastructure.document import docx_to_pdf_converter as converter_module


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


def test_build_libreoffice_export_command_uses_docx_path_and_output_dir() -> None:
    command = DocxToPdfConverter.build_libreoffice_export_command(
        libreoffice_command="/usr/bin/libreoffice",
        rendered_docx_path=Path("/tmp/invoice.docx"),
        output_path=Path("/tmp/exported/invoice.pdf"),
    )

    assert command == [
        "/usr/bin/libreoffice",
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--convert-to",
        "pdf",
        "--outdir",
        "/tmp/exported",
        "/tmp/invoice.docx",
    ]


def test_get_converter_backend_uses_pages_on_macos(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages_app_path = tmp_path / "Pages.app"
    pages_app_path.mkdir()

    monkeypatch.setattr(converter_module.sys, "platform", "darwin")
    monkeypatch.setattr(DocxToPdfConverter, "PAGES_APP_PATH", pages_app_path)

    assert DocxToPdfConverter.get_converter_backend() == DocxToPdfConverter.PAGES_BACKEND_NAME


def test_get_converter_backend_uses_libreoffice_off_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter_module.sys, "platform", "linux")
    monkeypatch.setattr(
        DocxToPdfConverter,
        "resolve_libreoffice_command",
        classmethod(lambda cls: "/usr/bin/libreoffice"),
    )

    assert DocxToPdfConverter.get_converter_backend() == DocxToPdfConverter.LIBREOFFICE_BACKEND_NAME


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
        "get_converter_backend",
        classmethod(lambda cls: cls.PAGES_BACKEND_NAME),
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


def test_convert_runs_libreoffice_step_with_resolved_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    rendered_docx_path = tmp_path / "invoice.docx"
    output_path = tmp_path / "invoice.pdf"
    rendered_docx_path.write_bytes(b"docx")
    output_path.write_bytes(b"old pdf")

    exported_paths: list[tuple[Path, Path]] = []

    monkeypatch.setattr(
        DocxToPdfConverter,
        "get_converter_backend",
        classmethod(lambda cls: cls.LIBREOFFICE_BACKEND_NAME),
    )

    def export_pdf(cls: type[DocxToPdfConverter], docx_path: Path, pdf_path: Path) -> None:
        exported_paths.append((docx_path, pdf_path))
        assert not pdf_path.exists()
        pdf_path.write_bytes(b"%PDF")

    monkeypatch.setattr(
        DocxToPdfConverter,
        "export_with_libreoffice",
        classmethod(export_pdf),
    )

    caplog.set_level(logging.INFO)

    DocxToPdfConverter.convert(rendered_docx_path, output_path)

    assert exported_paths == [(rendered_docx_path.resolve(), output_path.resolve())]
    assert output_path.read_bytes() == b"%PDF"
    assert "Starting DOCX to PDF conversion with LibreOffice" in caplog.text
    assert "Finished DOCX to PDF conversion with LibreOffice" in caplog.text


def test_ensure_pages_installed_raises_when_pages_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(DocxToPdfConverter, "PAGES_APP_PATH", tmp_path / "missing.app")

    with pytest.raises(FileNotFoundError, match=r"Pages\.app not found"):
        DocxToPdfConverter.ensure_pages_installed()


def test_resolve_libreoffice_command_raises_when_libreoffice_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter_module.shutil, "which", lambda command: None)

    with pytest.raises(FileNotFoundError, match="LibreOffice executable not found"):
        DocxToPdfConverter.resolve_libreoffice_command()


def test_validate_output_rejects_missing_and_empty_pdf(tmp_path: Path) -> None:
    missing_pdf = tmp_path / "missing.pdf"
    empty_pdf = tmp_path / "empty.pdf"
    valid_pdf = tmp_path / "valid.pdf"

    with pytest.raises(RuntimeError, match="DOCX to PDF converter did not create PDF"):
        DocxToPdfConverter.validate_output(missing_pdf)

    empty_pdf.touch()
    with pytest.raises(RuntimeError, match="Generated PDF is empty"):
        DocxToPdfConverter.validate_output(empty_pdf)

    valid_pdf.write_bytes(b"%PDF")
    DocxToPdfConverter.validate_output(valid_pdf)
