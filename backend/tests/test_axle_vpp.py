"""Tests for Axle VPP integration logic and rules safeguarding."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.core.settings_cache as sc
from app.core.optimizer import BatteryOptimizer, OptimizationInput, PricePeriod
from app.core.rules_engine import RulesEngine, SystemState as RulesState
from app.services.axle import axle_client


def test_vpp_precharge():
    """LP should Force Charge during a cheap early period ahead of a VPP export slot.

    Setup: period 0 is 2p (very cheap), periods 1–2 are 15p, period 3 is the VPP
    slot with 100p export rate. The optimizer should bulk-charge in period 0 so it
    can maximise export revenue during the VPP period.
    """
    base = datetime(2026, 4, 23, 0, 0, 0)
    prices = [
        PricePeriod(base, base + timedelta(minutes=30), 2.0, 2.0),      # Very cheap — charge here
        PricePeriod(base + timedelta(minutes=30), base + timedelta(minutes=60), 15.0, 15.0),
        PricePeriod(base + timedelta(minutes=60), base + timedelta(minutes=90), 15.0, 15.0),
        PricePeriod(base + timedelta(minutes=90), base + timedelta(minutes=120), 30.0, 100.0),  # VPP slot
    ]
    inp = OptimizationInput(
        battery_soc=20.0,
        solar_power_kw=0.0,
        prices=prices,
    )
    res = BatteryOptimizer().optimize(inp)
    assert res.optimization_status == "optimal"
    # Optimizer must pre-charge at cheap period 0 to maximise VPP export revenue
    assert res.recommended_mode == "Force Charge"


@pytest.mark.asyncio
async def test_axle_client_disabled_returns_none():
    """Axle client returns None if axle_vpp_enabled setting is false."""
    sc._cache["axle_vpp_enabled"] = "false"
    sc._cache["axle_vpp_token"] = "some-token"
    res = await axle_client.get_active_event()
    assert res is None


@pytest.mark.asyncio
async def test_axle_client_empty_token_returns_none():
    """Axle client returns None if token is empty."""
    sc._cache["axle_vpp_enabled"] = "true"
    sc._cache["axle_vpp_token"] = ""
    res = await axle_client.get_active_event()
    assert res is None


@pytest.mark.asyncio
async def test_axle_client_parses_event():
    """Axle client parses start_time and end_time JSON correctly into naive UTC datetimes."""
    sc._cache["axle_vpp_enabled"] = "true"
    sc._cache["axle_vpp_token"] = "mock-token"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "start_time": "2026-06-25T18:00:00Z",
        "end_time": "2026-06-25T20:00:00Z",
    }

    # Patch the get method on the shared client instance directly
    with patch.object(axle_client, "_get_client") as mock_get_client:
        mock_httpx_client = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_resp)
        mock_get_client.return_value = mock_httpx_client

        res = await axle_client.get_active_event()
        assert res is not None
        start, end = res
        assert start.year == 2026
        assert start.month == 6
        assert start.day == 25
        assert start.hour == 18
        assert end.hour == 20


@pytest.mark.asyncio
async def test_axle_client_null_response_returns_none():
    """Axle client returns None if API response payload is empty or invalid."""
    sc._cache["axle_vpp_enabled"] = "true"
    sc._cache["axle_vpp_token"] = "mock-token"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = None

    with patch.object(axle_client, "_get_client") as mock_get_client:
        mock_httpx_client = MagicMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_resp)
        mock_get_client.return_value = mock_httpx_client

        res = await axle_client.get_active_event()
        assert res is None


def test_vpp_slot_overlap_detection():
    """Test overlapping edge cases for detecting VPP slots."""
    # VPP event: 18:00 to 20:00
    vpp_start = datetime(2026, 6, 25, 18, 0, 0)
    vpp_end = datetime(2026, 6, 25, 20, 0, 0)

    # Slot fully inside: 18:30 to 19:00
    p1_start = datetime(2026, 6, 25, 18, 30, 0)
    p1_end = datetime(2026, 6, 25, 19, 0, 0)
    assert p1_start < vpp_end and p1_end > vpp_start

    # Slot fully outside: 17:00 to 17:30
    p2_start = datetime(2026, 6, 25, 17, 0, 0)
    p2_end = datetime(2026, 6, 25, 17, 30, 0)
    assert not (p2_start < vpp_end and p2_end > vpp_start)

    # Slot overlapping start: 17:45 to 18:15
    p3_start = datetime(2026, 6, 25, 17, 45, 0)
    p3_end = datetime(2026, 6, 25, 18, 15, 0)
    assert p3_start < vpp_end and p3_end > vpp_start

    # Slot overlapping end: 19:45 to 20:15
    p4_start = datetime(2026, 6, 25, 19, 45, 0)
    p4_end = datetime(2026, 6, 25, 20, 15, 0)
    assert p4_start < vpp_end and p4_end > vpp_start


def test_vpp_precharge_forces_charge_with_lead_time():
    """Low SOC + upcoming VPP event with enough lead time should hard-constrain
    the LP to charge up to the SOC required to sustain a full-length export.
    """
    base = datetime(2026, 4, 23, 18, 0, 0)
    # 6 periods (3 hours) of lead time, then a 1hr VPP event at 21:00-22:00.
    # Period 0 is the uniquely cheapest slot so the cost-minimising LP must
    # front-load charging there rather than spreading it arbitrarily across
    # equally-priced periods (which would leave charge_0 ambiguous).
    prices = []
    for i in range(6):
        prices.append(PricePeriod(
            base + timedelta(minutes=30 * i),
            base + timedelta(minutes=30 * (i + 1)),
            2.0 if i == 0 else 10.0, 15.0,
        ))
    vpp_start = base + timedelta(hours=3)
    vpp_end = vpp_start + timedelta(hours=1)
    for i in range(6, 10):
        prices.append(PricePeriod(
            base + timedelta(minutes=30 * i),
            base + timedelta(minutes=30 * (i + 1)),
            30.0, 100.0 if (base + timedelta(minutes=30*i)) < vpp_end and (base + timedelta(minutes=30*(i+1))) > vpp_start else 15.0,
        ))

    inp = OptimizationInput(
        battery_soc=15.0,  # Low SOC, like the real-world failure
        solar_power_kw=0.0,
        prices=prices,
        vpp_event=(vpp_start, vpp_end),
    )
    res = BatteryOptimizer().optimize(inp)
    assert res.optimization_status == "optimal"
    # With 3 hours of cheap lead time and a low battery, the optimizer must
    # Force Charge now to reach the pre-charge SOC target before the event.
    assert res.recommended_mode == "Force Charge"


def test_vpp_precharge_clips_gracefully_with_short_lead_time():
    """Very short lead time (or no lead time) before the VPP event must not make
    the LP infeasible — the required SOC is clipped to what's achievable.
    """
    base = datetime(2026, 4, 23, 21, 0, 0)
    # VPP event starts immediately (period 0 is the event) — zero lead time.
    vpp_start = base
    vpp_end = base + timedelta(hours=1)
    prices = [
        PricePeriod(base, base + timedelta(minutes=30), 30.0, 100.0),
        PricePeriod(base + timedelta(minutes=30), base + timedelta(hours=1), 30.0, 100.0),
        PricePeriod(base + timedelta(hours=1), base + timedelta(minutes=90), 15.0, 15.0),
    ]
    inp = OptimizationInput(
        battery_soc=15.0,
        solar_power_kw=0.0,
        prices=prices,
        vpp_event=(vpp_start, vpp_end),
    )
    res = BatteryOptimizer().optimize(inp)
    # No period exists fully before the event (target_idx is None) — LP must
    # still solve normally (no hard constraint added), not go infeasible.
    assert res.optimization_status == "optimal"


def test_vpp_precharge_disabled_setting_no_constraint():
    """axle_vpp_precharge_enabled=false should skip the hard constraint entirely,
    falling back to price-incentive-only behaviour (regression safety)."""
    sc._cache["axle_vpp_precharge_enabled"] = "false"
    base = datetime(2026, 4, 23, 18, 0, 0)
    prices = []
    for i in range(6):
        prices.append(PricePeriod(
            base + timedelta(minutes=30 * i),
            base + timedelta(minutes=30 * (i + 1)),
            15.0, 15.0,
        ))
    vpp_start = base + timedelta(hours=3)
    vpp_end = vpp_start + timedelta(hours=1)
    inp = OptimizationInput(
        battery_soc=15.0,
        solar_power_kw=0.0,
        prices=prices,
        vpp_event=(vpp_start, vpp_end),
    )
    res = BatteryOptimizer().optimize(inp)
    assert res.optimization_status == "optimal"
    sc._cache["axle_vpp_precharge_enabled"] = "true"  # restore for other tests


def test_no_vpp_event_unaffected():
    """No VPP event present — behaviour must be unchanged (regression safety)."""
    base = datetime(2026, 4, 23, 0, 0, 0)
    prices = [
        PricePeriod(base + timedelta(minutes=30 * i), base + timedelta(minutes=30 * (i + 1)), 15.0, 15.0)
        for i in range(10)
    ]
    inp = OptimizationInput(battery_soc=50.0, solar_power_kw=0.0, prices=prices)
    res = BatteryOptimizer().optimize(inp)
    assert res.optimization_status == "optimal"


def test_vpp_guard_disables_immersion():
    """The Rules Engine VPP Guard blocks immersion activation during active VPP events when configured."""
    engine = RulesEngine()
    device = MagicMock()
    state = RulesState(battery_soc=50.0, solar_power_kw=1.0, current_price_pence=15.0)

    # Enable VPP immersion disabling
    sc._cache["disable_immersion_during_vpp"] = "true"

    decision = engine.evaluate(
        device=device, state=state, current_temp=50.0, vpp_event_active=True
    )
    assert decision.action is False
    assert decision.source == "vpp_guard"
    assert "vpp" in decision.reason.lower()

    # Disable VPP immersion disabling -> should pass through
    sc._cache["disable_immersion_during_vpp"] = "false"
    decision = engine.evaluate(
        device=device, state=state, current_temp=50.0, vpp_event_active=True
    )
    # Falls back to default since no other rule matches
    assert decision.source == "default"
