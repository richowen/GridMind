"""Shared fixtures for GridMind test suite."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


def make_prices(n=48, base_pence=15.0, start_hour=0):
    """Build n half-hourly PricePeriod-like objects starting at start_hour UTC."""
    from app.core.optimizer import PricePeriod
    base = datetime(2026, 4, 23, start_hour, 0, 0)
    return [
        PricePeriod(
            valid_from=base + timedelta(minutes=30*i),
            valid_to=base + timedelta(minutes=30*(i+1)),
            price_pence=base_pence,
        )
        for i in range(n)
    ]


def make_varying_prices(values, start_hour=0):
    """Build prices from explicit list of pence values."""
    from app.core.optimizer import PricePeriod
    base = datetime(2026, 4, 23, start_hour, 0, 0)
    return [
        PricePeriod(
            valid_from=base + timedelta(minutes=30*i),
            valid_to=base + timedelta(minutes=30*(i+1)),
            price_pence=v,
        )
        for i, v in enumerate(values)
    ]


DEFAULTS = {
    "battery_capacity_kwh": "20.0",
    "battery_max_charge_kw": "10.5",
    "battery_max_discharge_kw": "5.0",
    "battery_efficiency": "0.95",
    "battery_min_soc": "10",
    "battery_max_soc": "100",
    "battery_voltage_v": "48.0",
    "grid_import_limit_kw": "15.0",
    "grid_export_limit_kw": "5.0",
    "export_price_pence": "15.0",
    "assumed_load_kw": "2.0",
    "force_charge_threshold_kw": "0.5",
    "force_discharge_threshold_kw": "0.5",
    "force_discharge_export_min_kw": "0.05",
    "optimization_horizon_hours": "24",
}


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Patch settings_cache so tests never need a DB connection."""
    import app.core.settings_cache as sc
    monkeypatch.setattr(sc, "_cache", dict(DEFAULTS))
    monkeypatch.setattr(sc, "_cache_time", float("inf"))
    return DEFAULTS
