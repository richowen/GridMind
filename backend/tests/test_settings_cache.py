"""Tests for settings_cache helper functions."""
import pytest
import app.core.settings_cache as sc


def test_get_setting_returns_value(mock_settings):
    assert sc.get_setting("battery_capacity_kwh") == "20.0"


def test_get_setting_default_when_missing():
    assert sc.get_setting("nonexistent_key", "fallback") == "fallback"


def test_get_setting_float(mock_settings):
    assert sc.get_setting_float("battery_capacity_kwh") == 20.0


def test_get_setting_float_default():
    assert sc.get_setting_float("missing_float", 99.9) == 99.9


def test_get_setting_int(mock_settings):
    assert sc.get_setting_int("battery_min_soc") == 10


def test_get_setting_int_default():
    assert sc.get_setting_int("missing_int", 42) == 42


def test_get_setting_bool_true(monkeypatch):
    monkeypatch.setattr(sc, "_cache", {"flag": "true"})
    monkeypatch.setattr(sc, "_cache_time", float("inf"))
    assert sc.get_setting_bool("flag") is True


def test_get_setting_bool_false(monkeypatch):
    monkeypatch.setattr(sc, "_cache", {"flag": "false"})
    monkeypatch.setattr(sc, "_cache_time", float("inf"))
    assert sc.get_setting_bool("flag") is False


def test_get_setting_bool_default():
    assert sc.get_setting_bool("missing_bool", True) is True


def test_invalidate_resets_ttl(monkeypatch):
    sc.invalidate_settings_cache()
    assert sc._cache_time == 0.0


def test_get_setting_float_bad_value(monkeypatch):
    monkeypatch.setattr(sc, "_cache", {"bad": "not_a_float"})
    monkeypatch.setattr(sc, "_cache_time", float("inf"))
    assert sc.get_setting_float("bad", 5.5) == 5.5


def test_get_setting_int_bad_value(monkeypatch):
    monkeypatch.setattr(sc, "_cache", {"bad": "nan"})
    monkeypatch.setattr(sc, "_cache_time", float("inf"))
    assert sc.get_setting_int("bad", 7) == 7
