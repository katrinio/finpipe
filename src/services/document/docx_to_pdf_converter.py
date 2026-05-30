import logging
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class DocxToPdfConverter:
    PAGES_APP_PATH = Path("/Applications/Pages.app")
    PAGES_EXPORT_TIMEOUT_SECONDS = 90

    @classmethod
    def convert(cls, rendered_docx_path: Path, output_path: Path) -> None:
        cls.ensure_pages_installed()

        rendered_docx_path = rendered_docx_path.resolve()
        output_path = output_path.resolve()

        LOGGER.info(
            "Starting DOCX to PDF conversion with Pages: docx=%s pdf=%s",
            rendered_docx_path,
            output_path,
        )
        cls.remove_existing_output(output_path)
        cls.open_with_pages(rendered_docx_path)
        cls.export_front_pages_document(rendered_docx_path, output_path)
        cls.validate_output(output_path)
        LOGGER.info(
            "Finished DOCX to PDF conversion with Pages: pdf=%s size=%s",
            output_path,
            output_path.stat().st_size,
        )

    @classmethod
    def ensure_pages_installed(cls) -> None:
        if cls.PAGES_APP_PATH.exists():
            LOGGER.debug("Pages.app found at %s", cls.PAGES_APP_PATH)
            return

        msg = "Pages.app not found"
        LOGGER.error("%s: %s", msg, cls.PAGES_APP_PATH)
        raise FileNotFoundError(msg)

    @classmethod
    def remove_existing_output(cls, output_path: Path) -> None:
        if not output_path.exists():
            return

        LOGGER.debug("Removing existing PDF before conversion: %s", output_path)
        output_path.unlink()

    @classmethod
    def open_with_pages(cls, rendered_docx_path: Path) -> None:
        LOGGER.debug("Opening DOCX with Pages: %s", rendered_docx_path)
        subprocess.run(
            ["open", "-a", "Pages", str(rendered_docx_path)],
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def export_front_pages_document(cls, rendered_docx_path: Path, output_path: Path) -> None:
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
    def validate_output(cls, output_path: Path) -> None:
        if not output_path.exists():
            msg = "Pages did not create PDF"
            LOGGER.error("%s: %s", msg, output_path)
            raise RuntimeError(msg)

        if output_path.stat().st_size == 0:
            msg = "Generated PDF is empty"
            LOGGER.error("%s: %s", msg, output_path)
            raise RuntimeError(msg)

    @classmethod
    def build_pages_export_script(cls, rendered_docx_path: Path, output_path: Path) -> list[str]:
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
    def build_osascript_command(cls, script_lines: list[str]) -> list[str]:
        command = ["osascript"]

        for line in script_lines:
            command.extend(["-e", line])

        return command
