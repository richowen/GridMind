"""Home Assistant REST API client. Reads sensor states and controls entities.
Depends on settings_cache for ha_url and ha_token."""

import logging
from typing import Optional

import httpx

from app.core.settings_cache import get_settings

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Thin async client for the HA REST API."""

    def _headers(self) -> dict:
        settings = get_settings()
        return {"Authorization": f"Bearer {settings['ha_token']}"}

    def _base_url(self) -> str:
        settings = get_settings()
        return settings["ha_url"].rstrip("/")

    async def get_state(self, entity_id: str) -> Optional[str]:
        """Return the state string for an entity, or None on error."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._base_url()}/api/states/{entity_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json().get("state")
        except Exception as e:
            logger.warning(f"HA get_state({entity_id}) failed: {e}")
            return None

    async def get_state_float(self, entity_id: str) -> Optional[float]:
        """Return entity state as float, or None on error."""
        state = await self.get_state(entity_id)
        try:
            return float(state) if state not in (None, "unavailable", "unknown") else None
        except (ValueError, TypeError):
            return None

    async def get_battery_soc(self) -> Optional[float]:
        settings = get_settings()
        return await self.get_state_float(settings["ha_entity_battery_soc"])

    async def get_battery_mode(self) -> Optional[str]:
        settings = get_settings()
        return await self.get_state(settings["ha_entity_battery_mode"])

    async def get_solar_power(self) -> Optional[float]:
        settings = get_settings()
        return await self.get_state_float(settings["ha_entity_solar_power"])

    async def get_solar_forecast_today(self) -> Optional[float]:
        settings = get_settings()
        return await self.get_state_float(settings["ha_entity_solar_forecast_today"])

    async def get_temperature(self, entity_id: str) -> Optional[float]:
        return await self.get_state_float(entity_id)

    async def get_switch_state(self, entity_id: str) -> Optional[bool]:
        state = await self.get_state(entity_id)
        if state == "on":
            return True
        if state == "off":
            return False
        return None

    async def set_battery_mode(self, mode: str) -> bool:
        """Set the Fox inverter work mode (Force Charge / Self Use)."""
        settings = get_settings()
        entity_id = settings["ha_entity_battery_mode"]
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._base_url()}/api/services/select/select_option",
                    headers=self._headers(),
                    json={"entity_id": entity_id, "option": mode},
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"HA set_battery_mode({mode}) failed: {e}")
            return False

    async def set_discharge_current(self, amps: int) -> bool:
        """Set the Fox inverter max discharge current."""
        settings = get_settings()
        entity_id = settings["ha_entity_discharge_current"]
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._base_url()}/api/services/number/set_value",
                    headers=self._headers(),
                    json={"entity_id": entity_id, "value": str(amps)},
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"HA set_discharge_current({amps}) failed: {e}")
            return False

    async def set_switch(self, entity_id: str, state: bool) -> bool:
        """Turn a switch on or off."""
        service = "turn_on" if state else "turn_off"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self._base_url()}/api/services/switch/{service}",
                    headers=self._headers(),
                    json={"entity_id": entity_id},
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"HA set_switch({entity_id}, {state}) failed: {e}")
            return False

    async def test_connection(self) -> dict:
        """Test HA connection. Returns {success, message}."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._base_url()}/api/",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return {"success": True, "message": "Connected to Home Assistant"}
        except Exception as e:
            return {"success": False, "message": str(e)}


ha_client = HomeAssistantClient()
