"""Pydantic schemas for electricity price API responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PriceOut(BaseModel):
    id: int
    valid_from: datetime
    valid_to: datetime
    price_pence: float
    classification: Optional[str] = None

    model_config = {"from_attributes": True}


class PriceStats(BaseModel):
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    negative_count: int
    cheap_count: int
    expensive_count: int
    total_periods: int
