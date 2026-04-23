"""Pydantic schemas for the stateless /dev/simulate endpoint."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class SimPrice(BaseModel):
    valid_from: datetime
    price_pence: float

class SimImmersionRule(BaseModel):
    rule_name: str = "rule"
    priority: int = 10
    action: str = "ON"
    logic_operator: str = "AND"
    is_enabled: bool = True
    price_enabled: bool = False
    price_operator: str = "<"
    price_threshold_pence: float = 15.0
    soc_enabled: bool = False
    soc_operator: str = ">"
    soc_threshold_percent: float = 50.0
    solar_enabled: bool = False
    solar_operator: str = ">"
    solar_threshold_kw: float = 2.0
    temp_enabled: bool = False
    temp_operator: str = "<"
    temp_threshold_c: float = 50.0
    time_enabled: bool = False
    time_start: str = "00:00"
    time_end: str = "23:59"

class SimImmersionInput(BaseModel):
    battery_soc: float = 60.0
    solar_power_kw: float = 3.0
    current_price_pence: float = 15.0
    current_temp_c: Optional[float] = None
    rules: List[SimImmersionRule] = []

class SimRequest(BaseModel):
    battery_soc: float = Field(50.0, ge=0, le=100)
    solar_power_kw: float = Field(10.6, ge=0)
    solar_profile: str = "sunny"
    solar_scale: float = Field(1.0, ge=0.0, le=1.0)
    live_charge_rate_kw: Optional[float] = None
    live_battery_voltage_v: Optional[float] = None
    battery_capacity_kwh: float = 20.0
    battery_max_charge_kw: float = 10.5
    battery_max_discharge_kw: float = 5.0
    battery_efficiency: float = 0.95
    battery_min_soc: int = 10
    battery_max_soc: int = 100
    battery_voltage_v: float = 48.0
    grid_import_limit_kw: float = 15.0
    grid_export_limit_kw: float = 5.0
    export_price_pence: float = 15.0
    assumed_load_kw: float = 2.0
    force_charge_threshold_kw: float = 0.5
    force_discharge_threshold_kw: float = 0.5
    force_discharge_export_min_kw: float = 0.05
    optimization_horizon_hours: int = 24
    prices: List[SimPrice] = []
    immersion: Optional[SimImmersionInput] = None

class SimPeriodResult(BaseModel):
    slot: int
    valid_from: str
    price_pence: float
    solar_kw: float
    charge_kw: float
    discharge_kw: float
    grid_import_kw: float
    grid_export_kw: float
    soc_kwh: float
    soc_pct: float

class SimImmersionResult(BaseModel):
    action: bool
    source: str
    reason: str

class SimResponse(BaseModel):
    recommended_mode: str
    decision_reason: str
    optimization_status: str
    objective_value: Optional[float]
    optimization_time_ms: float
    recommended_discharge_current: int
    periods: List[SimPeriodResult]
    immersion: Optional[SimImmersionResult] = None

# ── Why / Debug trace schemas ────────────────────────────────────────────────

class ConditionTrace(BaseModel):
    type: str
    enabled: bool
    skipped: bool
    actual_value: Optional[float] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    passed: Optional[bool] = None

class RuleTrace(BaseModel):
    rule_name: str
    priority: int
    enabled: bool
    action: str
    logic_operator: str
    matched: bool
    conditions: List[ConditionTrace]

class DeviceDebugResult(BaseModel):
    device_name: str
    device_id: int
    switch_entity_id: str
    temp_c: Optional[float] = None
    active_override: Optional[str] = None
    final_decision: SimImmersionResult
    rule_traces: List[RuleTrace]

class LpDecisionTrace(BaseModel):
    mode: str
    reason: str
    status: str
    current_slot_price_pence: Optional[float] = None
    battery_soc: Optional[float] = None
    solar_power_kw: Optional[float] = None
    objective_value: Optional[float] = None
    optimization_time_ms: Optional[float] = None
    last_run: Optional[str] = None

class WhyResponse(BaseModel):
    timestamp: str
    readings: dict
    lp_decision: LpDecisionTrace
    immersion_devices: List[DeviceDebugResult]
