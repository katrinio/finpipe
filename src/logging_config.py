"""Единая настройка логирования для CLI и workflow-скриптов."""

import logging

DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    """Включает базовое логирование с общим форматом сообщений."""

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
    )
