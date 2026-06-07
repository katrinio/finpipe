"""Подстановка плейсхолдеров в DOCX-шаблон без внешних зависимостей."""

import logging
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from src.utils.credentials import EnvVar

LOGGER = logging.getLogger(__name__)


class DocxTemplateRenderer:
    """Пересобирает DOCX, заменяя текстовые шаблонные поля."""

    @classmethod
    def render(
        cls,
        template_path: Path,
        output_path: Path,
        replacements: dict[str, str],
    ) -> None:
        """Рендерит новый DOCX-файл на основе шаблона и замен."""

        template_path = cls.resolve_project_path(template_path)
        output_path = cls.resolve_project_path(output_path)

        with (
            ZipFile(template_path, "r") as source,
            ZipFile(
                output_path,
                "w",
                compression=ZIP_DEFLATED,
            ) as target,
        ):
            for name in source.namelist():
                content = source.read(name)

                if name.endswith(".xml"):
                    text = content.decode("utf-8")

                    for placeholder, value in replacements.items():
                        text = text.replace(
                            placeholder,
                            value,
                        )

                    content = text.encode("utf-8")

                target.writestr(
                    name,
                    content,
                )

    @staticmethod
    def resolve_project_path(path: Path) -> Path:
        """Резолвит относительный путь от корня проекта."""

        if path.is_absolute():
            return path

        return EnvVar.PROJECT_ROOT / path
