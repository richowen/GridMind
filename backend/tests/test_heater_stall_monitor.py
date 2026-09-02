"""Tests for the heater stall monitor: alerts when a temperature-target heat call
isn't raising the real water temperature (e.g. a tripped safety switch)."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.core.settings_cache as sc
from app.core.heater_stall_monitor import _sessions, evaluate_stall


@pytest.fixture(autouse=True)
def _clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


def _settings(**overrides):
    sc._cache["heater_stall_alert_enabled"] = "true"
    sc._cache["heater_stall_check_minutes"] = "20"
    sc._cache["heater_stall_min_rise_c"] = "0.5"
    sc._cache.update(overrides)


def test_not_heating_for_temp_target_clears_session_and_returns_none():
    _settings()
    now = datetime(2026, 9, 2, 17, 0, 0)
    assert evaluate_stall(1, "Immersion 1", False, 40.0, now) is None
    assert 1 not in _sessions


def test_first_cycle_starts_session_no_alert():
    _settings()
    now = datetime(2026, 9, 2, 17, 0, 0)
    result = evaluate_stall(1, "Immersion 1", True, 40.0, now)
    assert result is None
    assert _sessions[1]["start_temp"] == 40.0
    assert _sessions[1]["start_time"] == now


def test_no_alert_before_check_window_elapses():
    _settings()
    start = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, start)
    result = evaluate_stall(1, "Immersion 1", True, 40.0, start + timedelta(minutes=10))
    assert result is None


def test_alert_fires_when_temp_stalled_past_check_window():
    _settings()
    start = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, start)
    result = evaluate_stall(1, "Immersion 1", True, 40.1, start + timedelta(minutes=21))
    assert result is not None
    assert "Immersion 1" in result
    assert "40.0" in result and "40.1" in result


def test_no_alert_when_temp_rises_enough():
    _settings()
    start = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, start)
    result = evaluate_stall(1, "Immersion 1", True, 42.0, start + timedelta(minutes=21))
    assert result is None


def test_alert_only_fires_once_per_session():
    _settings()
    start = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, start)
    first = evaluate_stall(1, "Immersion 1", True, 40.0, start + timedelta(minutes=21))
    second = evaluate_stall(1, "Immersion 1", True, 40.0, start + timedelta(minutes=25))
    assert first is not None
    assert second is None


def test_session_resets_after_heating_stops_then_restarts():
    _settings()
    start = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, start)
    evaluate_stall(1, "Immersion 1", True, 40.0, start + timedelta(minutes=21))  # alert fired
    # Heating stops (e.g. target satisfied or override) — session clears
    evaluate_stall(1, "Immersion 1", False, 40.0, start + timedelta(minutes=22))
    assert 1 not in _sessions
    # New heating session starts fresh — no immediate alert even though temp is flat
    result = evaluate_stall(1, "Immersion 1", True, 40.0, start + timedelta(minutes=23))
    assert result is None


def test_disabled_setting_suppresses_alert():
    _settings(heater_stall_alert_enabled="false")
    start = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, start)
    result = evaluate_stall(1, "Immersion 1", True, 40.0, start + timedelta(minutes=21))
    assert result is None


def test_current_temp_none_clears_session():
    _settings()
    now = datetime(2026, 9, 2, 17, 0, 0)
    evaluate_stall(1, "Immersion 1", True, 40.0, now)
    assert evaluate_stall(1, "Immersion 1", True, None, now + timedelta(minutes=5)) is None
    assert 1 not in _sessions


@pytest.mark.asyncio
async def test_discord_send_no_webhook_configured_returns_false():
    sc._cache["discord_webhook_url"] = ""
    from app.services.discord import send_discord_alert
    result = await send_discord_alert("test message")
    assert result is False


@pytest.mark.asyncio
async def test_discord_send_posts_to_webhook():
    sc._cache["discord_webhook_url"] = "https://discord.com/api/webhooks/123/abc"
    from app.services.discord import send_discord_alert

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await send_discord_alert("test message")
        assert result is True
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == "https://discord.com/api/webhooks/123/abc"
        assert kwargs["json"] == {"content": "test message"}


@pytest.mark.asyncio
async def test_discord_send_failure_returns_false():
    sc._cache["discord_webhook_url"] = "https://discord.com/api/webhooks/123/abc"
    from app.services.discord import send_discord_alert

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("network error"))
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await send_discord_alert("test message")
        assert result is False
