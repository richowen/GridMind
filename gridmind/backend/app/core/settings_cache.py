"""In-memory cache for system_settings with 60-second TTL.
Call invalidate_settings_cache() after any PUT /api/v1/settings request."""

import time
import logging
from typing import Dict

from app.database import SessionLocal
from app.models.settings import SystemSetting

logger = logging.getLogger(__name__)

_cache: Dict[str, str] = {}
_cache_time: float = 0.0
CACHE_TTL = 60.0  # seconds


def _load_from_db() -> Dict[str, str]:
    """Load all settings from DB as a flat {key: value} dict."""
    db = SessionLocal()
    try:
        rows = db.query(SystemSetting).all()
        return {row.key: row.value for row in rows}
    except Exception as e:
        logger.error(f"Failed to load settings from DB: {e}")
        return {}
    finally:
        db.close()


def get_settings() -> Dict[str, str]:
    """Return cached settings dict. Refreshes from DB if TTL expired."""
    global _cache, _cache_time
    if time.time() - _cache_time > CACHE_TTL:
        _cache = _load_from_db()
        _cache_time = time.time()
        logger.debug(f"Settings cache refreshed ({len(_cache)} keys)")
    return _cache


def invalidate_settings_cache() -> None:
    """Force cache refresh on next get_settings() call. Call after settings update."""
    global _cache_time
    _cache_time = 0.0


def get_setting(key: str, default: str = "") -> str:
    """Get a single setting value by key."""
    return get_settings().get(key, default)


def get_setting_float(key: str, default: float = 0.0) -> float:
    """Get a setting as float."""
    try:
        return float(get_settings().get(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_setting_int(key: str, default: int = 0) -> int:
    """Get a setting as int."""
    try:
        return int(get_settings().get(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_setting_bool(key: str, default: bool = False) -> bool:
    """Get a setting as bool."""
    val = get_settings().get(key, str(default)).lower()
    return val in ("true", "1", "yes")
