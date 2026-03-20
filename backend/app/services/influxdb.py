"""InfluxDB 2.x client for time-series logging. Backward-compatible with existing measurements.
Depends on settings_cache for connection details. All writes are optional (influx_enabled setting).

Uses a persistent InfluxDB client — recreated only when connection settings change — to avoid
creating a new HTTP connection pool on every write call."""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.settings_cache import get_settings, get_setting_bool

logger = logging.getLogger(__name__)

# Optional dependency — influxdb-client may not be installed in all environments.
# All write methods check _INFLUX_AVAILABLE before importing client objects.
try:
    from influxdb_client import InfluxDBClient as _InfluxClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    _INFLUX_AVAILABLE = True
except ImportError:
    _INFLUX_AVAILABLE = False
    logger.warning("influxdb-client not installed — InfluxDB writes disabled")


class InfluxDBClient:
    """Writes metrics to InfluxDB. Silently skips if disabled or unavailable."""

    def __init__(self):
        self._client = None
        # Track the settings key used to create the current client so we can
        # detect when influx_url or influx_token changes and recreate the client.
        self._client_settings_key: Optional[str] = None

    def _get_client(self):
        """Return a shared InfluxDB write client, recreating if settings changed."""
        settings = get_settings()
        settings_key = f"{settings.get('influx_url')}:{settings.get('influx_token')}:{settings.get('influx_org')}"
        if self._client is None or self._client_settings_key != settings_key:
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    pass
            self._client = _InfluxClient(
                url=settings["influx_url"],
                token=settings["influx_token"],
                org=settings["influx_org"],
            )
            self._client_settings_key = settings_key
        return self._client

    def _is_enabled(self) -> bool:
        return _INFLUX_AVAILABLE and get_setting_bool("influx_enabled", True)

    def write_prices(self, prices: list) -> None:
        """Write electricity prices to InfluxDB (existing measurement schema)."""
        if not self._is_enabled():
            return
        try:
            settings = get_settings()
            client = self._get_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            points = []
            for p in prices:
                point = (
                    Point("electricity_price")
                    .tag("classification", p["classification"])
                    .tag("is_negative", str(p["price_pence"] < 0).lower())
                    .field("price_pence", float(p["price_pence"]))
                    .field("price_pounds", float(p["price_pence"]) / 100)
                    .time(p["valid_from"])
                )
                points.append(point)
            write_api.write(bucket=settings["influx_bucket"], record=points)
        except Exception as e:
            logger.warning(f"InfluxDB write_prices failed: {e}")

    def write_system_state(self, state: dict) -> None:
        """Write system state snapshot to InfluxDB."""
        if not self._is_enabled():
            return
        try:
            settings = get_settings()
            client = self._get_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = (
                Point("system_state")
                .tag("battery_mode", state.get("battery_mode", "unknown"))
                .field("battery_soc", state.get("battery_soc"))
                .field("solar_power_kw", state.get("solar_power_kw"))
                .field("current_price_pence", state.get("current_price_pence"))
                .field("live_charge_rate_kw", state.get("live_charge_rate_kw"))
                .time(datetime.now(timezone.utc))
            )
            # Optional solar forecast fields
            if state.get("solar_forecast_today_kwh") is not None:
                point = point.field("solar_forecast_today_kwh", state["solar_forecast_today_kwh"])
            if state.get("solar_forecast_next_hour_kw") is not None:
                point = point.field("solar_forecast_next_hour_kw", state["solar_forecast_next_hour_kw"])
            write_api.write(bucket=settings["influx_bucket"], record=point)
        except Exception as e:
            logger.warning(f"InfluxDB write_system_state failed: {e}")

    def write_immersion_state(self, device_name: str, is_on: bool, temp_c: Optional[float] = None) -> None:
        """Write per-device immersion state snapshot to InfluxDB.

        Replaces the old hardcoded immersion_main_on / immersion_lucy_on fields
        with a generic per-device measurement keyed by device_name tag.
        """
        if not self._is_enabled():
            return
        try:
            settings = get_settings()
            client = self._get_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = (
                Point("immersion_state")
                .tag("device_name", device_name)
                .field("is_on", is_on)
                .time(datetime.now(timezone.utc))
            )
            if temp_c is not None:
                point = point.field("temp_c", temp_c)
            write_api.write(bucket=settings["influx_bucket"], record=point)
        except Exception as e:
            logger.warning(f"InfluxDB write_immersion_state({device_name}) failed: {e}")

    def write_immersion_action(self, device_name: str, decision: dict) -> None:
        """Write immersion action event (new measurement)."""
        if not self._is_enabled():
            return
        try:
            settings = get_settings()
            client = self._get_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = (
                Point("immersion_action")
                .tag("device_name", device_name)
                .tag("action", "on" if decision.get("action") else "off")
                .tag("source", decision.get("source", "unknown"))
                .field("success", True)
                .field("reason", decision.get("reason", ""))
                .time(datetime.now(timezone.utc))
            )
            write_api.write(bucket=settings["influx_bucket"], record=point)
        except Exception as e:
            logger.warning(f"InfluxDB write_immersion_action failed: {e}")

    async def test_connection(self) -> dict:
        """Test InfluxDB connectivity."""
        if not _INFLUX_AVAILABLE:
            return {"success": False, "message": "influxdb-client not installed"}
        try:
            client = self._get_client()
            health = client.health()
            return {"success": health.status == "pass", "message": f"InfluxDB status: {health.status}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


influx_client = InfluxDBClient()
