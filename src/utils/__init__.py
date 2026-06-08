"""Утилиты общего назначения, используемые в разных слоях проекта."""

from __future__ import annotations

__all__ = ["Utils"]

from src.utils.utils import Utils


def __getattr__(name: str):
    if name == "Utils":
        return Utils

    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
