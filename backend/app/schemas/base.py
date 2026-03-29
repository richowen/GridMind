"""Shared Pydantic base model for GridMind API schemas.

All datetime fields in API responses are stored as naive UTC in MariaDB.
This base model serialises them with a trailing 'Z' so that JavaScript's
``new Date("2026-03-29T19:40:00Z")`` correctly interprets them as UTC and
converts to the browser's local timezone (e.g. BST = UTC+1 in summer).

Without the 'Z', ``new Date("2026-03-29T19:40:00")`` is treated as *local*
time by modern browsers, causing timestamps to display one hour behind during
BST (clocks-forward period).
"""

import re
from datetime import datetime
from typing import Any
from pydantic import BaseModel, model_serializer

# Matches naive ISO 8601 datetime strings (no timezone suffix).
# Examples: "2026-03-29T19:40:00", "2026-03-29T19:40:00.123456"
_NAIVE_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$"
)


class UTCModel(BaseModel):
    """Base model that serialises naive datetime fields as UTC ISO strings with 'Z' suffix.

    Uses a wrap model_serializer so that all datetime values in the output dict
    are post-processed to append 'Z' before the JSON response is sent.
    """

    model_config = {"from_attributes": True}

    @model_serializer(mode="wrap")
    def _append_utc_z(self, handler: Any) -> Any:
        """Walk the serialised dict and append 'Z' to all naive datetime ISO strings."""
        result = handler(self)
        if isinstance(result, dict):
            return {k: _fix_dt(v) for k, v in result.items()}
        return result


def _fix_dt(value: Any) -> Any:
    """Append 'Z' to a naive datetime or naive ISO datetime string.

    Handles two cases:
    1. ``datetime`` object with no tzinfo — convert to ISO + 'Z'
    2. Already-serialised string matching naive ISO format — append 'Z'
       (Pydantic v2 may convert datetime → str before our serializer runs)
    """
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.isoformat() + "Z"
    if isinstance(value, str) and _NAIVE_ISO_RE.match(value):
        return value + "Z"
    return value
