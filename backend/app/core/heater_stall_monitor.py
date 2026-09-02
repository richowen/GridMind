"""Detects an immersion heater that is commanded ON by a temperature target but
whose real water temperature is not rising — e.g. a tripped thermal safety
switch silently prevents heating even though GridMind believes the switch is on.

Tracks per-device heating sessions in memory (module-level, reset on restart)
and returns an alert message the first time a session is confirmed stalled."""

import logging
from datetime import datetime
from typing import Dict, Optional

from app.core.settings_cache import get_setting_bool, get_setting_float, get_setting_int

logger = logging.getLogger(__name__)

# {device_id: {"start_time": datetime, "start_temp": float, "alert_sent": bool}}
_sessions: Dict[int, dict] = {}


def evaluate_stall(
    device_id: int,
    device_label: str,
    is_temp_target_heating: bool,
    current_temp: Optional[float],
    now: datetime,
) -> Optional[str]:
    """Call once per evaluation cycle for a device.

    Returns an alert message the first time a heating session driven by a
    temperature target fails to raise the water temperature enough within the
    configured check window, else None. Session state resets whenever the
    device is no longer being driven by a temperature target.
    """
    if not is_temp_target_heating or current_temp is None:
        _sessions.pop(device_id, None)
        return None

    session = _sessions.get(device_id)
    if session is None:
        _sessions[device_id] = {"start_time": now, "start_temp": current_temp, "alert_sent": False}
        return None

    if session["alert_sent"] or not get_setting_bool("heater_stall_alert_enabled", True):
        return None

    check_minutes = get_setting_int("heater_stall_check_minutes", 20)
    elapsed_minutes = (now - session["start_time"]).total_seconds() / 60
    if elapsed_minutes < check_minutes:
        return None

    min_rise = get_setting_float("heater_stall_min_rise_c", 0.5)
    rise = current_temp - session["start_temp"]
    if rise >= min_rise:
        return None

    session["alert_sent"] = True
    return (
        f"⚠️ {device_label}: water temp has not risen while heating for a "
        f"temperature target. Started at {session['start_temp']:.1f}°C, now "
        f"{current_temp:.1f}°C after {int(elapsed_minutes)} min. "
        f"Check the heater element / safety switch."
    )
