"""Конвертация DOCX в PDF через Pages на macOS или LibreOffice в CI."""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class DocxToPdfConverter:
    """Выбирает доступный backend и конвертирует DOCX в PDF."""

    PAGES_BACKEND_NAME = "Pages"
    LIBREOFFICE_BACKEND_NAME = "LibreOffice"
    PAGES_APP_PATH = Path("/Applications/Pages.app")
    LIBREOFFICE_COMMANDS = ("soffice", "libreoffice")
    PAGES_EXPORT_TIMEOUT_SECONDS = 90
    LIBREOFFICE_EXPORT_TIMEOUT_SECONDS = 90

    @classmethod
    def convert(cls, rendered_docx_path: Path, output_path: Path) -> None:
        """Конвертирует DOCX-файл в PDF и проверяет результат."""

        rendered_docx_path = rendered_docx_path.resolve()
        output_path = output_path.resolve()
        converter_backend = cls.get_converter_backend()

        LOGGER.info(
            "Starting DOCX to PDF conversion with %s: docx=%s pdf=%s",
            converter_backend,
            rendered_docx_path,
            output_path,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cls.remove_existing_output(output_path)
        cls.export_pdf(
            converter_backend=converter_backend,
            rendered_docx_path=rendered_docx_path,
            output_path=output_path,
        )
        cls.validate_output(output_path, converter_backend)
        LOGGER.info(
            "Finished DOCX to PDF conversion with %s: pdf=%s size=%s",
            converter_backend,
            output_path,
            output_path.stat().st_size,
        )

    @classmethod
    def get_converter_backend(cls) -> str:
        """Возвращает доступный backend конвертации для текущей ОС."""

        if cls.should_use_pages():
            cls.ensure_pages_installed()
            return cls.PAGES_BACKEND_NAME

        cls.ensure_libreoffice_installed()
        return cls.LIBREOFFICE_BACKEND_NAME

    @classmethod
    def should_use_pages(cls) -> bool:
        """Определяет, следует ли использовать Pages вместо LibreOffice."""

        return sys.platform == "darwin"

    @classmethod
    def export_pdf(cls, converter_backend: str, rendered_docx_path: Path, output_path: Path) -> None:
        """Запускает экспорт через выбранный backend."""

        if converter_backend == cls.PAGES_BACKEND_NAME:
            cls.open_with_pages(rendered_docx_path)
            cls.export_front_pages_document(rendered_docx_path, output_path)
            return

        if converter_backend == cls.LIBREOFFICE_BACKEND_NAME:
            cls.export_with_libreoffice(rendered_docx_path, output_path)
            return

        msg = f"Unsupported DOCX to PDF converter backend: {converter_backend}"
        raise ValueError(msg)

    @classmethod
    def ensure_pages_installed(cls) -> None:
        """Проверяет наличие Pages.app на macOS."""

        if cls.PAGES_APP_PATH.exists():
            LOGGER.debug("Pages.app found at %s", cls.PAGES_APP_PATH)
            return

        msg = "Pages.app not found"
        LOGGER.error("%s: %s", msg, cls.PAGES_APP_PATH)
        raise FileNotFoundError(msg)

    @classmethod
    def ensure_libreoffice_installed(cls) -> None:
        """Проверяет, что LibreOffice доступен в PATH."""

        cls.resolve_libreoffice_command()

    @classmethod
    def resolve_libreoffice_command(cls) -> str:
        """Находит исполняемый файл LibreOffice среди известных имён."""

        for command in cls.LIBREOFFICE_COMMANDS:
            executable_path = shutil.which(command)
            if executable_path is not None:
                LOGGER.debug("LibreOffice executable found: %s", executable_path)
                return executable_path

        msg = "LibreOffice executable not found"
        LOGGER.error("%s: tried %s", msg, ", ".join(cls.LIBREOFFICE_COMMANDS))
        raise FileNotFoundError(msg)

    @classmethod
    def has_available_converter(cls) -> bool:
        """Возвращает True, если в среде есть хотя бы один backend."""

        if cls.should_use_pages():
            return cls.PAGES_APP_PATH.exists()

        return any(shutil.which(command) is not None for command in cls.LIBREOFFICE_COMMANDS)

    @classmethod
    def remove_existing_output(cls, output_path: Path) -> None:
        """Удаляет старый PDF перед новой конвертацией."""

        if not output_path.exists():
            return

        LOGGER.debug("Removing existing PDF before conversion: %s", output_path)
        output_path.unlink()

    @classmethod
    def open_with_pages(cls, rendered_docx_path: Path) -> None:
        """Открывает DOCX в Pages перед экспортом."""

        LOGGER.debug("Opening DOCX with Pages: %s", rendered_docx_path)
        subprocess.run(
            ["open", "-a", "Pages", str(rendered_docx_path)],
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def export_front_pages_document(cls, rendered_docx_path: Path, output_path: Path) -> None:
        """Экспортирует активный документ Pages в PDF через AppleScript."""

        LOGGER.debug("Exporting front Pages document to PDF: %s", output_path)
        subprocess.run(
            cls.build_osascript_command(
                cls.build_pages_export_script(
                    rendered_docx_path=rendered_docx_path,
                    output_path=output_path,
                )
            ),
            check=True,
            capture_output=True,
            text=True,
            timeout=cls.PAGES_EXPORT_TIMEOUT_SECONDS,
        )

    @classmethod
    def export_with_libreoffice(cls, rendered_docx_path: Path, output_path: Path) -> None:
        """Конвертирует DOCX в PDF через headless LibreOffice."""

        LOGGER.debug("Exporting DOCX to PDF with LibreOffice: %s", output_path)
        generated_output_path = output_path.parent / f"{rendered_docx_path.stem}.pdf"
        if generated_output_path != output_path:
            cls.remove_existing_output(generated_output_path)

        subprocess.run(
            cls.build_libreoffice_export_command(
                libreoffice_command=cls.resolve_libreoffice_command(),
                rendered_docx_path=rendered_docx_path,
                output_path=output_path,
            ),
            check=True,
            capture_output=True,
            text=True,
            timeout=cls.LIBREOFFICE_EXPORT_TIMEOUT_SECONDS,
        )

        if generated_output_path != output_path and generated_output_path.exists():
            generated_output_path.replace(output_path)

    @classmethod
    def validate_output(cls, output_path: Path, converter_backend: str = "DOCX to PDF converter") -> None:
        """Проверяет, что конвертер действительно создал непустой PDF."""

        if not output_path.exists():
            msg = f"{converter_backend} did not create PDF"
            LOGGER.error("%s: %s", msg, output_path)
            raise RuntimeError(msg)

        if output_path.stat().st_size == 0:
            msg = "Generated PDF is empty"
            LOGGER.error("%s: %s", msg, output_path)
            raise RuntimeError(msg)

    @classmethod
    def build_pages_export_script(cls, rendered_docx_path: Path, output_path: Path) -> list[str]:
        """Собирает AppleScript для экспорта текущего документа Pages."""

        return [
            'tell application "Pages"',
            "activate",
            f'open POSIX file "{rendered_docx_path}"',
            "delay 2",
            "set docRef to front document",
            f'export docRef to POSIX file "{output_path}" as PDF',
            "close docRef saving no",
            "end tell",
        ]

    @classmethod
    def build_libreoffice_export_command(cls, libreoffice_command: str, rendered_docx_path: Path, output_path: Path) -> list[str]:
        """Собирает команду запуска LibreOffice в headless-режиме."""

        return [
            libreoffice_command,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_path.parent),
            str(rendered_docx_path),
        ]

    @classmethod
    def build_osascript_command(cls, script_lines: list[str]) -> list[str]:
        """Преобразует список строк AppleScript в команду `osascript`."""

        command = ["osascript"]

        for line in script_lines:
            command.extend(["-e", line])

        return command
