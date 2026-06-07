"""Подготовка словаря замен для DOCX-шаблонов."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any, cast


class Replacement:
    """Преобразует модели и словари в набор плейсхолдеров шаблона."""

    @classmethod
    def build_replacements(cls, data: object) -> dict[str, str]:
        """Строит словарь вида `{{field}} -> value` для шаблона."""

        template_data = cls.to_template_data(data)

        return {f"{{{{{field_name}}}}}": str(value) for field_name, value in template_data.items()}

    @classmethod
    def to_template_data(cls, data: object) -> dict[str, object]:
        """Нормализует dataclass или mapping в обычный словарь."""

        if is_dataclass(data) and not isinstance(data, type):
            return cast("dict[str, object]", asdict(cast("Any", data)))

        if isinstance(data, Mapping):
            return dict(data)

        msg = "Template data must be a mapping or dataclass instance"
        raise TypeError(msg)
