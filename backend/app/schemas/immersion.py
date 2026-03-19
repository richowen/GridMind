"""Pydantic schemas for immersion devices, smart rules, and temperature targets."""

from datetime import datetime, time
from typing import List, Optional
from pydantic import BaseModel


class ImmersionDeviceOut(BaseModel):
    id: int
    name: str
    display_name: str
    switch_entity_id: str
    temp_sensor_entity_id: Optional[str] = None
    is_enabled: bool = True  # default True handles legacy NULL rows from MariaDB
    sort_order: int = 0

    model_config = {"from_attributes": True}


class ImmersionDeviceCreate(BaseModel):
    name: str
    display_name: str
    switch_entity_id: str
    temp_sensor_entity_id: Optional[str] = None
    is_enabled: bool = True
    sort_order: int = 0


class ImmersionDeviceUpdate(BaseModel):
    display_name: Optional[str] = None
    switch_entity_id: Optional[str] = None
    temp_sensor_entity_id: Optional[str] = None
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class SmartRuleOut(BaseModel):
    id: int
    immersion_id: int
    rule_name: str
    is_enabled: bool = True
    priority: int = 10
    action: str
    logic_operator: str = "AND"
    price_enabled: bool = False
    price_operator: Optional[str] = None
    price_threshold_pence: Optional[float] = None
    soc_enabled: bool = False
    soc_operator: Optional[str] = None
    soc_threshold_percent: Optional[float] = None
    solar_enabled: bool = False
    solar_operator: Optional[str] = None
    solar_threshold_kw: Optional[float] = None
    temp_enabled: bool = False
    temp_operator: Optional[str] = None
    temp_threshold_c: Optional[float] = None
    time_enabled: bool = False
    time_start: Optional[time] = None
    time_end: Optional[time] = None

    model_config = {"from_attributes": True}


class SmartRuleCreate(BaseModel):
    rule_name: str
    is_enabled: bool = True
    priority: int = 10
    action: str  # 'ON' or 'OFF'
    logic_operator: str = "AND"
    price_enabled: bool = False
    price_operator: Optional[str] = None
    price_threshold_pence: Optional[float] = None
    soc_enabled: bool = False
    soc_operator: Optional[str] = None
    soc_threshold_percent: Optional[float] = None
    solar_enabled: bool = False
    solar_operator: Optional[str] = None
    solar_threshold_kw: Optional[float] = None
    temp_enabled: bool = False
    temp_operator: Optional[str] = None
    temp_threshold_c: Optional[float] = None
    time_enabled: bool = False
    time_start: Optional[time] = None
    time_end: Optional[time] = None


class TempTargetOut(BaseModel):
    id: int
    immersion_id: int
    target_name: str
    target_temp_c: float
    target_time: time
    days_of_week: str
    heating_rate_c_per_hour: float = 5.0
    buffer_minutes: int = 30
    is_enabled: bool = True

    model_config = {"from_attributes": True}


class TempTargetCreate(BaseModel):
    target_name: str
    target_temp_c: float
    target_time: time
    days_of_week: str
    heating_rate_c_per_hour: float = 5.0
    buffer_minutes: int = 30
    is_enabled: bool = True


class DeviceStatusOut(BaseModel):
    device: ImmersionDeviceOut
    current_temp_c: Optional[float] = None
    switch_state: Optional[bool] = None
    active_rule: Optional[str] = None
    decision_source: Optional[str] = None
