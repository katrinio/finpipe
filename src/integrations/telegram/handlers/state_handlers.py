from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class StateHandler:
    """Обработчик состояния ожидания файла."""

    handler: Callable[..., None]
    error_message: str
