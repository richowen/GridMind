"""Octopus Energy Agile API client. Fetches half-hourly electricity prices.
Depends on settings_cache for product, tariff, and region codes."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from app.core.settings_cache import get_settings

logger = logging.getLogger(__name__)

OCTOPUS_API_BASE = "https://api.octopus.energy/v1"


class OctopusEnergyClient:
    """Fetches Agile tariff prices from the Octopus Energy API."""

    def _get_tariff_url(self) -> str:
        settings = get_settings()
        product = settings["octopus_product"]
        tariff = settings["octopus_tariff"]
        return f"{OCTOPUS_API_BASE}/products/{product}/electricity-tariffs/{tariff}/standard-unit-rates/"

    async def fetch_prices(self, hours_ahead: int = 48) -> List[dict]:
        """Fetch upcoming Agile prices. Returns list of {valid_from, valid_to, price_pence}."""
        now = datetime.now(timezone.utc)
        period_from = now.replace(minute=0, second=0, microsecond=0)
        period_to = period_from + timedelta(hours=hours_ahead)

        params = {
            "period_from": period_from.isoformat(),
            "period_to": period_to.isoformat(),
            "page_size": 200,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(self._get_tariff_url(), params=params)
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])
            prices = []
            settings = get_settings()
            neg_threshold = float(settings.get("price_negative_threshold", "0"))
            cheap_threshold = float(settings.get("price_cheap_threshold", "10"))
            exp_threshold = float(settings.get("price_expensive_threshold", "25"))

            for item in results:
                price_pence = item["value_inc_vat"]
                classification = self._classify(price_pence, neg_threshold, cheap_threshold, exp_threshold)
                prices.append({
                    "valid_from": item["valid_from"],
                    "valid_to": item["valid_to"],
                    "price_pence": price_pence,
                    "classification": classification,
                })

            logger.info(f"Fetched {len(prices)} Octopus price periods")
            return prices

        except Exception as e:
            logger.error(f"Octopus price fetch failed: {e}")
            return []

    def _classify(self, price: float, neg: float, cheap: float, expensive: float) -> str:
        if price < neg:
            return "negative"
        if price < cheap:
            return "cheap"
        if price > expensive:
            return "expensive"
        return "normal"

    async def test_connection(self) -> dict:
        """Test Octopus API connectivity."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self._get_tariff_url(), params={"page_size": 1})
                resp.raise_for_status()
                return {"success": True, "message": "Connected to Octopus Energy API"}
        except Exception as e:
            return {"success": False, "message": str(e)}


octopus_client = OctopusEnergyClient()
