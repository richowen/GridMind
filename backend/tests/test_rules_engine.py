"""Tests for RulesEngine immersion decision logic."""
import pytest
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock

from app.core.rules_engine import RulesEngine, SystemState, ImmersionDecision
from app.utils import utcnow

engine = RulesEngine()
DEVICE = MagicMock(name="Immersion 1")


def _make_override(desired=True, minutes_remaining=60):
    ov = MagicMock()
    ov.desired_state = desired
    ov.expires_at = utcnow() + timedelta(minutes=minutes_remaining)
    return ov


def _make_rule(enabled=True, priority=10, action="ON",
               price_enabled=False, price_op="<", price_thresh=10.0,
               soc_enabled=False, soc_op=">", soc_thresh=50.0,
               solar_enabled=False, solar_op=">", solar_thresh=2.0,
               temp_enabled=False, temp_op="<", temp_thresh=50.0,
               time_enabled=False, time_start=time(0,0), time_end=time(23,59),
               logic="AND"):
    r = MagicMock()
    r.is_enabled = enabled
    r.priority = priority
    r.action = action
    r.rule_name = "test_rule"
    r.price_enabled = price_enabled; r.price_operator = price_op; r.price_threshold_pence = price_thresh
    r.soc_enabled = soc_enabled; r.soc_operator = soc_op; r.soc_threshold_percent = soc_thresh
    r.solar_enabled = solar_enabled; r.solar_operator = solar_op; r.solar_threshold_kw = solar_thresh
    r.temp_enabled = temp_enabled; r.temp_operator = temp_op; r.temp_threshold_c = temp_thresh
    r.time_enabled = time_enabled; r.time_start = time_start; r.time_end = time_end
    r.logic_operator = logic
    return r


def _make_temp_target(enabled=True, target_temp=55.0, current_temp=40.0,
                      target_time_offset_hours=2, heating_rate=5.0, buffer=15):
    t = MagicMock()
    t.is_enabled = enabled
    t.target_temp_c = target_temp
    t.heating_rate_c_per_hour = heating_rate
    t.buffer_minutes = buffer
    now = datetime.now()
    t.target_time = (now + timedelta(hours=target_time_offset_hours)).time()
    t.days_of_week = str(now.weekday())
    return t


STATE = SystemState(battery_soc=60.0, solar_power_kw=3.0, current_price_pence=10.0)


def test_manual_override_wins():
    ov = _make_override(desired=True)
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, active_override=ov)
    assert d.action is True
    assert d.source == "manual_override"


def test_manual_override_off():
    ov = _make_override(desired=False)
    d = engine.evaluate(DEVICE, STATE, current_temp=60.0, active_override=ov)
    assert d.action is False
    assert d.source == "manual_override"


def test_default_off_when_no_rules():
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0)
    assert d.action is False
    assert d.source == "default"


def test_smart_rule_price_match():
    rule = _make_rule(price_enabled=True, price_op="<", price_thresh=12.0)
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, smart_rules=[rule])
    assert d.action is True
    assert d.source == "smart_rule"


def test_smart_rule_price_no_match():
    rule = _make_rule(price_enabled=True, price_op="<", price_thresh=5.0)
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, smart_rules=[rule])
    assert d.action is False
    assert d.source == "default"


def test_smart_rule_or_logic_partial_match():
    rule = _make_rule(
        price_enabled=True, price_op="<", price_thresh=5.0,  # no match: 10 > 5
        solar_enabled=True, solar_op=">", solar_thresh=2.0,   # match: 3 > 2
        logic="OR",
    )
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, smart_rules=[rule])
    assert d.action is True


def test_smart_rule_and_logic_requires_all():
    rule = _make_rule(
        price_enabled=True, price_op="<", price_thresh=5.0,   # no match
        solar_enabled=True, solar_op=">", solar_thresh=2.0,   # match
        logic="AND",
    )
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, smart_rules=[rule])
    assert d.action is False


def test_temp_target_triggers_heating():
    target = _make_temp_target(current_temp=40.0, target_temp=55.0,
                               target_time_offset_hours=1, heating_rate=20.0)
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, temp_targets=[target])
    assert d.action is True
    assert d.source == "temperature_target"


def test_temp_target_no_heating_when_warm_enough():
    target = _make_temp_target(current_temp=60.0, target_temp=55.0,
                               target_time_offset_hours=1, heating_rate=20.0)
    d = engine.evaluate(DEVICE, STATE, current_temp=60.0, temp_targets=[target])
    assert d.action is False


def test_disabled_rule_ignored():
    rule = _make_rule(enabled=False, price_enabled=True, price_op="<", price_thresh=100.0)
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, smart_rules=[rule])
    assert d.source == "default"


def test_priority_ordering():
    r_low = _make_rule(priority=20, action="OFF", price_enabled=True, price_op="<", price_thresh=100.0)
    r_high = _make_rule(priority=5, action="ON", solar_enabled=True, solar_op=">", solar_thresh=1.0)
    d = engine.evaluate(DEVICE, STATE, current_temp=40.0, smart_rules=[r_low, r_high])
    assert d.action is True  # high priority (5) runs first
