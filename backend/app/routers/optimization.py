"""Optimization router: recommendation, prices, and current system state endpoints."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.optimization import OptimizationResult, SystemState
from app.models.prices import ElectricityPrice
from app.schemas.optimization import OptimizationResultOut, SystemStateOut, CurrentStateOut
from app.schemas.prices import PriceOut, PriceStats
from app.utils import utcnow

router = APIRouter(tags=["optimization"])


@router.get("/recommendation/now", response_model=OptimizationResultOut)
def get_current_recommendation(db: Session = Depends(get_db)):
    """Return the most recent optimization result."""
    result = (
        db.query(OptimizationResult)
        .order_by(OptimizationResult.timestamp.desc())
        .first()
    )
    if not result:
        # Return a minimal dict; timestamp will be serialised with 'Z' by OptimizationResultOut
        return {"id": 0, "timestamp": utcnow(), "optimization_status": "no_data"}
    return result


@router.get("/prices/current", response_model=List[PriceOut])
def get_current_prices(hours: int = 48, db: Session = Depends(get_db)):
    """Return upcoming electricity prices for the next N hours."""
    now = utcnow()  # DB stores naive UTC datetimes
    prices = (
        db.query(ElectricityPrice)
        .filter(ElectricityPrice.valid_to >= now)
        .order_by(ElectricityPrice.valid_from)
        .limit(hours * 2)
        .all()
    )
    return prices


@router.get("/prices/stats", response_model=PriceStats)
def get_price_stats(db: Session = Depends(get_db)):
    """Return statistics for today's prices."""
    import statistics
    now = utcnow()  # DB stores naive UTC datetimes
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    prices = (
        db.query(ElectricityPrice)
        .filter(ElectricityPrice.valid_from >= today_start)
        .all()
    )
    if not prices:
        return PriceStats(min_price=0, max_price=0, mean_price=0, median_price=0,
                          negative_count=0, cheap_count=0, expensive_count=0, total_periods=0)
    vals = [p.price_pence for p in prices]
    return PriceStats(
        min_price=min(vals),
        max_price=max(vals),
        mean_price=statistics.mean(vals),
        median_price=statistics.median(vals),
        negative_count=sum(1 for p in prices if p.classification == "negative"),
        cheap_count=sum(1 for p in prices if p.classification == "cheap"),
        expensive_count=sum(1 for p in prices if p.classification == "expensive"),
        total_periods=len(prices),
    )


@router.post("/prices/refresh")
async def trigger_price_refresh():
    """Manually trigger a price refresh from Octopus API."""
    from app.core.scheduler import price_refresh
    await price_refresh()
    return {"status": "ok", "message": "Price refresh triggered"}


@router.get("/state/current", response_model=SystemStateOut)
def get_current_state(db: Session = Depends(get_db)):
    """Return the most recent system state snapshot."""
    state = (
        db.query(SystemState)
        .order_by(SystemState.timestamp.desc())
        .first()
    )
    return state
