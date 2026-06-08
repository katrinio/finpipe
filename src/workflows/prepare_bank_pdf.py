"""Backward-compatible alias for the bank request workflow."""

from __future__ import annotations

import sys

from src.workflows import process_bank_request as _process_bank_request

sys.modules[__name__] = _process_bank_request
