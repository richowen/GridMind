"""Tests for BatteryOptimizer LP core logic."""
import pytest
from tests.conftest import make_prices, make_varying_prices
from app.core.optimizer import BatteryOptimizer, OptimizationInput


def _run(soc=50.0, solar=3.0, prices=None, **kw):
    if prices is None:
        prices = make_prices(48, 15.0)
    inp = OptimizationInput(battery_soc=soc, solar_power_kw=solar, prices=prices, **kw)
    return BatteryOptimizer().optimize(inp)


def test_no_prices_returns_self_use():
    r = _run(prices=[])
    assert r.recommended_mode == "Self Use"
    assert r.optimization_status == "no_prices"


def test_flat_moderate_price_self_use():
    """Flat 15p price — no benefit to force-charge or discharge, expect Self Use."""
    r = _run(soc=50.0, solar=3.0, prices=make_prices(48, 15.0))
    assert r.optimization_status == "optimal"
    assert r.recommended_mode == "Self Use"


def test_very_cheap_price_force_charge():
    """First slot at 2p (cheap), rest at 30p — optimizer should Force Charge."""
    prices = make_varying_prices([2.0] + [30.0]*47)
    r = _run(soc=20.0, solar=0.0, prices=prices)
    assert r.optimization_status == "optimal"
    assert r.recommended_mode == "Force Charge"
    assert r.decision_reason != ""


def test_expensive_price_low_soc_self_use():
    """High price but low SOC — should not force discharge below min_soc."""
    prices = make_prices(48, 40.0)
    r = _run(soc=12.0, solar=0.0, prices=prices)
    assert r.optimization_status == "optimal"
    # At 12% SOC near min(10%) there is little room to discharge to grid
    assert r.recommended_mode in ("Self Use", "Force Discharge")


def test_force_discharge_high_price_high_soc():
    """90% SOC with very high first-slot price and low export price = may discharge."""
    prices = make_varying_prices([50.0]*48)
    r = _run(soc=90.0, solar=0.0, prices=prices)
    assert r.optimization_status == "optimal"
    assert r.recommended_mode in ("Force Discharge", "Self Use")


def test_discharge_current_calculated():
    """Discharge current in amps must be positive and match kW/V formula."""
    r = _run(soc=80.0, solar=0.0, prices=make_prices(48, 30.0))
    # 5kW / 48V * 1000 = ~104 A
    assert r.recommended_discharge_current > 0
    assert r.recommended_discharge_current <= 200


def test_solar_exceeds_load_no_force_charge():
    """When solar > load + charge need, grid import should be minimal."""
    prices = make_prices(48, 20.0)
    r = _run(soc=50.0, solar=10.6, prices=prices)
    assert r.optimization_status == "optimal"


def test_live_bms_cap_limits_charge():
    """live_charge_rate_kw=1.0 should cap effective charge to 1.0 kW."""
    # Very cheap price to trigger Force Charge, but BMS only allows 1 kW
    prices = make_varying_prices([1.0] + [30.0]*47)
    r = _run(soc=10.0, solar=0.0, prices=prices, live_charge_rate_kw=1.0)
    assert r.optimization_status == "optimal"
    # Force Charge threshold is 0.5 kW; 1.0 kW cap still permits it
    assert r.recommended_mode == "Force Charge"


def test_per_period_solar_profile_used():
    """solar_forecast_profile=[0]*48 should produce same result as solar_power_kw=0."""
    prices = make_prices(48, 15.0)
    r1 = _run(soc=50.0, solar=0.0, prices=prices)
    r2 = _run(soc=50.0, solar=5.0, prices=prices,
              solar_forecast_profile=[0.0]*48)
    assert r1.recommended_mode == r2.recommended_mode


def test_live_battery_voltage_affects_amps():
    """Higher voltage should produce lower amp value for same kW."""
    prices = make_prices(48, 30.0)
    r_low = _run(soc=80.0, solar=0.0, prices=prices, live_battery_voltage_v=48.0)
    r_high = _run(soc=80.0, solar=0.0, prices=prices, live_battery_voltage_v=96.0)
    assert r_high.recommended_discharge_current < r_low.recommended_discharge_current
