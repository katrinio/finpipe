import logging

DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
    )
