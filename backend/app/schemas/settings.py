"""Pydantic schemas for system settings API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.base import UTCModel


class SettingOut(UTCModel):
    key: str
    value: str
    value_type: str
    category: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


class SettingUpdate(BaseModel):
    value: str


class SettingsBulkUpdate(BaseModel):
    settings: Dict[str, str]  # {key: value}


class SettingsGrouped(BaseModel):
    """Settings grouped by category for the Settings page."""
    battery: List[SettingOut] = []
    ha: List[SettingOut] = []
    ha_entities: List[SettingOut] = []
    octopus: List[SettingOut] = []
    prices: List[SettingOut] = []
    optimization: List[SettingOut] = []
    influxdb: List[SettingOut] = []
    system: List[SettingOut] = []


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
