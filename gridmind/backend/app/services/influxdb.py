"""InfluxDB 2.x client for time-series logging. Backward-compatible with existing measurements.
Depends on settings_cache for connection details. All writes are optional (influx_enabled setting)."""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.settings_cache import get_settings

logger = logging.getLogger(__name__)


class InfluxDBClient:
    """Writes metrics to InfluxDB. Silently skips if disabled or unavailable."""

    def _get_client(self):
        """Create an InfluxDB write client from current settings."""
        from influxdb_client import InfluxDBClient as _Client
        settings = get_settings()
        return _Client(
            url=settings["influx_url"],
            token=settings["influx_token"],
            org=settings["influx_org"],
        )

    def _is_enabled(self) -> bool:
        settings = get_settings()
        return settings.get("influx_enabled", "true").lower() == "true"

    def write_prices(self, prices: list) -> None:
        """Write electricity prices to InfluxDB (existing measurement schema)."""
        if not self._is_enabled():
            return
        try:
            from influxdb_client.client.write_api import SYNCHRONOUS
            settings = get_settings()
            client = self._get_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            from influxdb_client import Point
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
            client.close()
        except Exception as e:
            logger.warning(f"InfluxDB write_prices failed: {e}")

    def write_system_state(self, state: dict) -> None:
        """Write system state snapshot (existing measurement schema + new temp fields)."""
        if not self._is_enabled():
            return
        try:
            from influxdb_client.client.write_api import SYNCHRONOUS
            from influxdb_client import Point
            settings = get_settings()
            client = self._get_client()
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = (
                Point("system_state")
                .tag("battery_mode", state.get("battery_mode", "unknown"))
                .field("battery_soc", state.get("battery_soc"))
                .field("solar_power_kw", state.get("solar_power_kw"))
                .field("current_price_pence", state.get("current_price_pence"))
                .field("immersion_main_on", state.get("immersion_main_on"))
                .field("immersion_lucy_on", state.get("immersion_lucy_on"))
                .time(datetime.now(timezone.utc))
            )
            # New optional temperature fields (additive only)
            if state.get("temp_main_c") is not None:
                point = point.field("temp_main_c", state["temp_main_c"])
            if state.get("temp_lucy_c") is not None:
                point = point.field("temp_lucy_c", state["temp_lucy_c"])
            write_api.write(bucket=settings["influx_bucket"], record=point)
            client.close()
        except Exception as e:
            logger.warning(f"InfluxDB write_system_state failed: {e}")

    def write_immersion_action(self, device_name: str, decision: dict) -> None:
        """Write immersion action event (new measurement)."""
        if not self._is_enabled():
            return
        try:
            from influxdb_client.client.write_api import SYNCHRONOUS
            from influxdb_client import Point
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
            client.close()
        except Exception as e:
            logger.warning(f"InfluxDB write_immersion_action failed: {e}")

    async def test_connection(self) -> dict:
        """Test InfluxDB connectivity."""
        try:
            client = self._get_client()
            health = client.health()
            client.close()
            return {"success": health.status == "pass", "message": f"InfluxDB status: {health.status}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


influx_client = InfluxDBClient()
