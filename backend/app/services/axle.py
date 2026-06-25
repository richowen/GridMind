"""Axle Energy VPP API Client.

Fetches active virtual power plant (VPP) export event windows.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

import httpx

from app.core.settings_cache import get_setting, get_setting_bool

logger = logging.getLogger(__name__)


class AxleVPPClient:
    """Async client for fetching Axle VPP event details."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        # Recreate the client if the token changes
        self._client_settings_key: Optional[str] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return a shared httpx.AsyncClient, recreating if token changed."""
        import asyncio
        token = get_setting("axle_vpp_token", "")
        if self._client is None or self._client.is_closed or self._client_settings_key != token:
            if self._client and not self._client.is_closed:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._client.aclose())
                except RuntimeError:
                    pass  # No running loop - let GC handle it
            self._client = httpx.AsyncClient(timeout=10)
            self._client_settings_key = token
        return self._client

    async def get_active_event(self) -> Optional[Tuple[datetime, datetime]]:
        """Fetch the active VPP event start and end UTC times.

        Returns None if disabled, token is empty, 401 occurs, or request fails.
        """
        enabled = get_setting_bool("axle_vpp_enabled", False)
        token = get_setting("axle_vpp_token", "")
        if not enabled or not token.strip():
            return None

        try:
            client = self._get_client()
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                "https://api.axle.energy/vpp/home-assistant/event",
                headers=headers,
            )
            if resp.status_code == 401:
                logger.warning("Axle VPP API returned 401 Unauthorized")
                return None
            resp.raise_for_status()

            data = resp.json()
            if not data or not isinstance(data, dict):
                return None

            start_str = data.get("start_time")
            end_str = data.get("end_time")
            if not start_str or not end_str:
                return None

            # Parse and convert to naive UTC datetime
            def to_naive_utc(dt_str: str) -> datetime:
                if dt_str.endswith("Z"):
                    dt_str = dt_str[:-1] + "+00:00"
                dt = datetime.fromisoformat(dt_str)
                return dt.astimezone(timezone.utc).replace(tzinfo=None)

            return to_naive_utc(start_str), to_naive_utc(end_str)
        except Exception as e:
            logger.warning(f"Axle VPP get_active_event failed: {e}")
            return None


axle_client = AxleVPPClient()
