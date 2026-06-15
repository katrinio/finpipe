"""Помощники для безопасного удаления временных файлов и директорий."""

import logging
import shutil
from pathlib import Path


def delete_file(path: Path, logger: logging.Logger) -> None:
    """Удаляет файл и логирует успешное удаление."""

    try:
        path.unlink()
    except FileNotFoundError:
        return

    logger.info("Deleted temporary file: %s", path)


def delete_directory(path: Path, logger: logging.Logger) -> None:
    """Удаляет директорию и логирует успешное удаление."""

    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        return

    logger.info("Deleted temporary directory: %s", path)
