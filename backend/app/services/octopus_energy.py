"""Octopus Energy Agile API client. Fetches half-hourly electricity prices.
Depends on settings_cache for product, tariff, and region codes.

Price classification uses percentage-based thresholds relative to the fetched
batch's min/max price range, so cheap/expensive labels adapt to price variation
within the window rather than relying on fixed absolute p/kWh values.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx

from app.core.settings_cache import get_settings

logger = logging.getLogger(__name__)

OCTOPUS_API_BASE = "https://api.octopus.energy/v1"


def _parse_dt(iso_str: str) -> datetime:
    """Parse an ISO 8601 datetime string (with or without Z suffix) into a naive UTC datetime.
    MariaDB DateTime columns do not accept timezone-aware datetimes or the Z suffix."""
    # Replace trailing Z with +00:00 so fromisoformat handles it on Python < 3.11
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    # Strip tzinfo — MariaDB DateTime is naive; we store everything as UTC
    return dt.replace(tzinfo=None)


def classify_prices(prices: List[dict], settings: dict) -> List[dict]:
    """Classify a batch of prices using percentage-based min/max thresholds.

    Each price is positioned within the batch's min-max range:
        position = (price - batch_min) / (batch_max - batch_min)  [0.0 – 1.0]

    The classification window is determined by the caller — pass a single day's
    prices for day-relative labels, or a multi-period window for a broader view.

    Classification:
        - price < neg_threshold (absolute p/kWh)  → 'negative'
        - position < cheap_pct / 100              → 'cheap'
        - position > expensive_pct / 100          → 'expensive'
        - otherwise                               → 'normal'

    When all prices are identical (batch_max == batch_min) every price is 'normal'.

    Args:
        prices: list of dicts with at least a 'price_pence' key.
        settings: dict from settings_cache (must contain the threshold keys).

    Returns:
        The same list with a 'classification' key added/updated on each dict.
    """
    if not prices:
        return prices

    neg_threshold = float(settings.get("price_negative_threshold", "0"))
    cheap_pct = float(settings.get("price_cheap_percent_threshold", "33")) / 100.0
    expensive_pct = float(settings.get("price_expensive_percent_threshold", "67")) / 100.0

    price_values = [p["price_pence"] for p in prices]
    day_min = min(price_values)
    day_max = max(price_values)
    price_range = day_max - day_min

    for p in prices:
        price = p["price_pence"]
        if price < neg_threshold:
            p["classification"] = "negative"
        elif price_range == 0:
            # All prices identical — classify everything as normal
            p["classification"] = "normal"
        else:
            position = (price - day_min) / price_range
            if position < cheap_pct:
                p["classification"] = "cheap"
            elif position > expensive_pct:
                p["classification"] = "expensive"
            else:
                p["classification"] = "normal"

    return prices


def get_current_price_classification(
    price_rows: list,
    now: datetime,
    settings: dict,
) -> Optional[str]:
    """Return the classification string for the current price period, or None.

    Shared helper used by optimization_loop and WebSocketManager.handle to avoid
    duplicating the classify → find-current-period logic in both places.

    Args:
        price_rows: SQLAlchemy ElectricityPrice ORM rows (must have valid_from,
                    valid_to, price_pence attributes).
        now:        Current naive UTC datetime for period matching.
        settings:   Settings dict from settings_cache (for threshold keys).
    """
    if not price_rows:
        return None
    batch = [{"price_pence": p.price_pence} for p in price_rows]
    classify_prices(batch, settings)
    current_idx = next(
        (i for i, p in enumerate(price_rows) if p.valid_from <= now <= p.valid_to),
        None,
    )
    return batch[current_idx].get("classification") if current_idx is not None else None


class OctopusEnergyClient:
    """Fetches Agile tariff prices from the Octopus Energy API."""

    def _get_tariff_url(self) -> str:
        settings = get_settings()
        product = settings["octopus_product"]
        tariff = settings["octopus_tariff"]
        return f"{OCTOPUS_API_BASE}/products/{product}/electricity-tariffs/{tariff}/standard-unit-rates/"

    async def fetch_prices(self, hours_ahead: int = 48) -> List[dict]:
        """Fetch upcoming Agile prices. Returns list of {valid_from, valid_to, price_pence, classification}."""
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
            settings = get_settings()

            prices = [
                {
                    "valid_from": _parse_dt(item["valid_from"]),
                    "valid_to": _parse_dt(item["valid_to"]),
                    "price_pence": item["value_inc_vat"],
                    "classification": None,  # filled in by classify_prices below
                }
                for item in results
            ]

            # Classify all prices relative to the full batch's min/max range
            classify_prices(prices, settings)

            logger.info(f"Fetched {len(prices)} Octopus price periods")
            return prices

        except Exception as e:
            logger.error(f"Octopus price fetch failed: {e}")
            return []

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
