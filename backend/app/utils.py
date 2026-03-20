"""Shared utility helpers for the GridMind backend."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (timezone-stripped).

    Replaces the deprecated ``datetime.utcnow()`` (removed in Python 3.14).
    MariaDB DateTime columns do not store timezone info, so we strip tzinfo
    after constructing an aware datetime — the value is still correct UTC.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
