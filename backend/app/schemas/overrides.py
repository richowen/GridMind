"""Pydantic schemas for manual override API requests and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ManualOverrideOut(BaseModel):
    id: int
    immersion_id: int
    immersion_name: str
    is_active: bool
    desired_state: bool
    source: str
    created_at: datetime
    expires_at: datetime
    cleared_at: Optional[datetime] = None
    cleared_by: Optional[str] = None

    model_config = {"from_attributes": True}


class ManualOverrideCreate(BaseModel):
    immersion_id: int
    desired_state: bool
    duration_minutes: int = 120  # Default 2 hours


class OverrideStatusOut(BaseModel):
    immersion_id: int
    immersion_name: str
    has_active_override: bool
    override: Optional[ManualOverrideOut] = None
    time_remaining_minutes: Optional[int] = None
