"""Помощники для безопасного удаления временных файлов и директорий."""

import logging
from pathlib import Path


def delete_file(path: Path, logger: logging.Logger) -> None:
    """Удаляет файл и логирует успешное удаление."""

    try:
        path.unlink()
    except FileNotFoundError:
        return

    logger.info("Deleted temporary file: %s", path)
