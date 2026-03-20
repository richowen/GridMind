"""Overrides router: manual override set/clear for immersion devices."""

from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.immersion import ImmersionDevice
from app.models.overrides import ManualOverride
from app.schemas.overrides import ManualOverrideOut, ManualOverrideCreate, OverrideStatusOut
from app.utils import utcnow

router = APIRouter(prefix="/overrides", tags=["overrides"])


@router.post("/manual/set", response_model=ManualOverrideOut, status_code=201)
def set_manual_override(body: ManualOverrideCreate, db: Session = Depends(get_db)):
    """Set a manual override for an immersion device."""
    device = db.query(ImmersionDevice).filter(ImmersionDevice.id == body.immersion_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Clear any existing active override for this device
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    now = utcnow()
    db.query(ManualOverride).filter(
        ManualOverride.immersion_id == body.immersion_id,
        ManualOverride.is_active == True,
    ).update({"is_active": False, "cleared_at": now, "cleared_by": "new_override"})

    override = ManualOverride(
        immersion_id=body.immersion_id,
        immersion_name=device.name,
        is_active=True,
        desired_state=body.desired_state,
        source="user",
        expires_at=now + timedelta(minutes=body.duration_minutes),
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


@router.get("/manual/status", response_model=List[OverrideStatusOut])
def get_override_status(db: Session = Depends(get_db)):
    """Return override status for all devices."""
    devices = db.query(ImmersionDevice).all()
    results = []
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    now = utcnow()
    for device in devices:
        active = (
            db.query(ManualOverride)
            .filter(
                ManualOverride.immersion_id == device.id,
                ManualOverride.is_active == True,
                ManualOverride.expires_at > now,
            )
            .first()
        )
        remaining = None
        if active:
            remaining = int((active.expires_at - now).total_seconds() / 60)
        results.append(OverrideStatusOut(
            immersion_id=device.id,
            immersion_name=device.name,
            has_active_override=active is not None,
            override=active,
            time_remaining_minutes=remaining,
        ))
    return results


@router.post("/manual/clear/{device_id}")
def clear_override(device_id: int, db: Session = Depends(get_db)):
    """Clear active override for a specific device."""
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    updated = db.query(ManualOverride).filter(
        ManualOverride.immersion_id == device_id,
        ManualOverride.is_active == True,
    ).update({"is_active": False, "cleared_at": utcnow(), "cleared_by": "user"})
    db.commit()
    return {"cleared": updated}


@router.post("/manual/clear-all")
def clear_all_overrides(db: Session = Depends(get_db)):
    """Clear all active overrides."""
    # DB stores naive UTC datetimes — use utcnow() for comparisons
    updated = db.query(ManualOverride).filter(
        ManualOverride.is_active == True,
    ).update({"is_active": False, "cleared_at": utcnow(), "cleared_by": "user"})
    db.commit()
    return {"cleared": updated}
