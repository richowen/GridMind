"""Pydantic schemas for optimization results and system state API responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OptimizationResultOut(BaseModel):
    id: int
    timestamp: datetime
    current_soc: Optional[float] = None
    current_solar_kw: Optional[float] = None
    current_price_pence: Optional[float] = None
    recommended_mode: Optional[str] = None
    recommended_discharge_current: Optional[int] = None
    optimization_status: Optional[str] = None
    optimization_time_ms: Optional[float] = None
    objective_value: Optional[float] = None
    decision_reason: Optional[str] = None
    next_action_time: Optional[datetime] = None  # Next scheduled optimization run

    model_config = {"from_attributes": True}


class SystemStateOut(BaseModel):
    id: int
    timestamp: datetime
    battery_soc: Optional[float] = None
    battery_mode: Optional[str] = None
    solar_power_kw: Optional[float] = None
    solar_forecast_today_kwh: Optional[float] = None
    solar_forecast_next_hour_kw: Optional[float] = None  # From Solcast 1hr forecast
    current_price_pence: Optional[float] = None
    # Note: immersion_main_on / immersion_lucy_on removed — per-device state is
    # logged to InfluxDB immersion_states measurement instead.

    model_config = {"from_attributes": True}


class CurrentStateOut(BaseModel):
    """Combined live state for the dashboard."""
    battery_soc: Optional[float] = None
    battery_mode: Optional[str] = None
    solar_power_kw: Optional[float] = None
    solar_forecast_today_kwh: Optional[float] = None
    solar_forecast_next_hour_kw: Optional[float] = None
    current_price_pence: Optional[float] = None
    price_classification: Optional[str] = None
    recommended_mode: Optional[str] = None
    decision_reason: Optional[str] = None
    last_updated: Optional[datetime] = None
