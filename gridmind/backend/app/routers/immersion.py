"""Immersion router: device registry, smart rules, and temperature targets CRUD."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.immersion import ImmersionDevice, ImmersionSmartRule, TemperatureTarget
from app.schemas.immersion import (
    ImmersionDeviceOut, ImmersionDeviceCreate, ImmersionDeviceUpdate,
    SmartRuleOut, SmartRuleCreate,
    TempTargetOut, TempTargetCreate,
    DeviceStatusOut,
)

router = APIRouter(prefix="/immersions", tags=["immersion"])


# ── Devices ──────────────────────────────────────────────────────────────────

@router.get("/devices", response_model=List[ImmersionDeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(ImmersionDevice).order_by(ImmersionDevice.sort_order).all()


@router.post("/devices", response_model=ImmersionDeviceOut, status_code=201)
def create_device(body: ImmersionDeviceCreate, db: Session = Depends(get_db)):
    device = ImmersionDevice(**body.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.put("/devices/{device_id}", response_model=ImmersionDeviceOut)
def update_device(device_id: int, body: ImmersionDeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(ImmersionDevice).filter(ImmersionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/devices/{device_id}", status_code=204)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(ImmersionDevice).filter(ImmersionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()


@router.get("/devices/{device_id}/status", response_model=DeviceStatusOut)
async def get_device_status(device_id: int, db: Session = Depends(get_db)):
    """Return live status including current temperature from HA."""
    from app.services.home_assistant import ha_client
    device = db.query(ImmersionDevice).filter(ImmersionDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    temp = None
    switch_state = None
    if device.temp_sensor_entity_id:
        temp = await ha_client.get_temperature(device.temp_sensor_entity_id)
    switch_state = await ha_client.get_switch_state(device.switch_entity_id)
    return DeviceStatusOut(device=device, current_temp_c=temp, switch_state=switch_state)


# ── Smart Rules ───────────────────────────────────────────────────────────────

@router.get("/{device_id}/rules", response_model=List[SmartRuleOut])
def list_rules(device_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ImmersionSmartRule)
        .filter(ImmersionSmartRule.immersion_id == device_id)
        .order_by(ImmersionSmartRule.priority)
        .all()
    )


@router.post("/{device_id}/rules", response_model=SmartRuleOut, status_code=201)
def create_rule(device_id: int, body: SmartRuleCreate, db: Session = Depends(get_db)):
    rule = ImmersionSmartRule(immersion_id=device_id, **body.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{device_id}/rules/{rule_id}", response_model=SmartRuleOut)
def update_rule(device_id: int, rule_id: int, body: SmartRuleCreate, db: Session = Depends(get_db)):
    rule = db.query(ImmersionSmartRule).filter(
        ImmersionSmartRule.id == rule_id,
        ImmersionSmartRule.immersion_id == device_id,
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in body.model_dump().items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{device_id}/rules/{rule_id}", status_code=204)
def delete_rule(device_id: int, rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ImmersionSmartRule).filter(
        ImmersionSmartRule.id == rule_id,
        ImmersionSmartRule.immersion_id == device_id,
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()


# ── Temperature Targets ───────────────────────────────────────────────────────

@router.get("/{device_id}/targets", response_model=List[TempTargetOut])
def list_targets(device_id: int, db: Session = Depends(get_db)):
    return db.query(TemperatureTarget).filter(TemperatureTarget.immersion_id == device_id).all()


@router.post("/{device_id}/targets", response_model=TempTargetOut, status_code=201)
def create_target(device_id: int, body: TempTargetCreate, db: Session = Depends(get_db)):
    target = TemperatureTarget(immersion_id=device_id, **body.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.put("/{device_id}/targets/{target_id}", response_model=TempTargetOut)
def update_target(device_id: int, target_id: int, body: TempTargetCreate, db: Session = Depends(get_db)):
    target = db.query(TemperatureTarget).filter(
        TemperatureTarget.id == target_id,
        TemperatureTarget.immersion_id == device_id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    for field, value in body.model_dump().items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{device_id}/targets/{target_id}", status_code=204)
def delete_target(device_id: int, target_id: int, db: Session = Depends(get_db)):
    target = db.query(TemperatureTarget).filter(
        TemperatureTarget.id == target_id,
        TemperatureTarget.immersion_id == device_id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
