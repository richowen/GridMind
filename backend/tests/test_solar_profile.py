"""Tests for _build_solar_forecast_profile in scheduler."""
import pytest
from datetime import datetime, timedelta

from app.core.scheduler import _build_solar_forecast_profile
from app.core.optimizer import PricePeriod


def _prices_utc(start_hour=6, n=48):
    base = datetime(2026, 4, 23, start_hour, 0, 0)
    return [
        PricePeriod(
            valid_from=base + timedelta(minutes=30*i),
            valid_to=base + timedelta(minutes=30*(i+1)),
            price_pence=15.0,
        )
        for i in range(n)
    ]


def test_no_forecast_returns_constant():
    prices = _prices_utc(start_hour=6)
    profile = _build_solar_forecast_profile(prices, solar_now_kw=5.0, solar_forecast_remaining_kwh=None)
    assert all(v == 5.0 for v in profile)
    assert len(profile) == 48


def test_zero_forecast_returns_constant():
    prices = _prices_utc(start_hour=6)
    profile = _build_solar_forecast_profile(prices, solar_now_kw=4.0, solar_forecast_remaining_kwh=0.0)
    assert all(v == 4.0 for v in profile)


def test_forecast_integral_approximates_kwh():
    """Sum of kW * 0.5hr should roughly equal forecast_remaining_kwh."""
    prices = _prices_utc(start_hour=0, n=48)  # full day from midnight
    kwh = 30.0
    profile = _build_solar_forecast_profile(prices, solar_now_kw=3.0, solar_forecast_remaining_kwh=kwh)
    total = sum(v * 0.5 for v in profile)
    assert abs(total - kwh) < 0.5  # within 0.5 kWh tolerance


def test_night_slots_are_zero():
    """Slots outside 5:00-20:00 local (UTC in BST = +1) should be 0."""
    # Midnight UTC = 1am BST — should be night slots
    prices = _prices_utc(start_hour=0, n=10)
    profile = _build_solar_forecast_profile(prices, solar_now_kw=5.0, solar_forecast_remaining_kwh=20.0)
    # UTC 00:00–04:00 = BST 01:00–05:00 = night
    for i in range(8):  # first 8 slots = 0:00–4:00 UTC
        assert profile[i] == 0.0, f"slot {i} should be 0 (night)"
