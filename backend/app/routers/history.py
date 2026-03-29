"""History router: optimization history, system state history, and action audit log."""

from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.actions import SystemAction
from app.models.optimization import OptimizationResult, SystemState
from app.schemas.optimization import OptimizationResultOut, SystemStateOut
from app.utils import utcnow

router = APIRouter(tags=["history"])


@router.get("/history/recommendations", response_model=List[OptimizationResultOut])
def get_recommendation_history(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Return optimization decision history for the last N hours."""
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    since = utcnow() - timedelta(hours=hours)
    return (
        db.query(OptimizationResult)
        .filter(OptimizationResult.timestamp >= since)
        .order_by(OptimizationResult.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/history/states", response_model=List[SystemStateOut])
def get_state_history(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """Return system state history for the last N hours."""
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    since = utcnow() - timedelta(hours=hours)
    return (
        db.query(SystemState)
        .filter(SystemState.timestamp >= since)
        .order_by(SystemState.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/history/actions")
def get_action_history(
    hours: int = Query(24, ge=1, le=720),
    action_type: Optional[str] = None,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Return HA action audit log for the last N hours."""
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    since = utcnow() - timedelta(hours=hours)
    query = db.query(SystemAction).filter(SystemAction.timestamp >= since)
    if action_type:
        query = query.filter(SystemAction.action_type == action_type)
    actions = query.order_by(SystemAction.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat() + "Z",
            "action_type": a.action_type,
            "entity_id": a.entity_id,
            "old_value": a.old_value,
            "new_value": a.new_value,
            "source": a.source,
            "reason": a.reason,
            "success": a.success,
        }
        for a in actions
    ]


@router.get("/stats/daily")
def get_daily_stats(db: Session = Depends(get_db)):
    """Return summary statistics for today."""
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    actions_today = db.query(SystemAction).filter(SystemAction.timestamp >= today).count()
    decisions_today = db.query(OptimizationResult).filter(OptimizationResult.timestamp >= today).count()
    return {
        "date": today.date().isoformat(),
        "optimization_runs": decisions_today,
        "ha_actions": actions_today,
    }
