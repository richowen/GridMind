"""System router: settings CRUD, connection tests, system control (pause/resume/optimize-now)."""

import json
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.settings_cache import invalidate_settings_cache
from app.database import get_db
from app.models.settings import SystemSetting
from app.schemas.settings import SettingOut, SettingUpdate, SettingsBulkUpdate, SettingsGrouped, ConnectionTestResult

router = APIRouter(tags=["system"])

# ── Settings ──────────────────────────────────────────────────────────────────

@router.get("/settings", response_model=SettingsGrouped)
def get_all_settings(db: Session = Depends(get_db)):
    """Return all settings grouped by category."""
    rows = db.query(SystemSetting).all()
    grouped = SettingsGrouped()
    for row in rows:
        category = row.category
        if hasattr(grouped, category):
            getattr(grouped, category).append(row)
    return grouped


@router.put("/settings")
def update_settings_bulk(body: SettingsBulkUpdate, db: Session = Depends(get_db)):
    """Update multiple settings at once."""
    for key, value in body.settings.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    db.commit()
    invalidate_settings_cache()
    return {"updated": len(body.settings)}


@router.get("/settings/{key}", response_model=SettingOut)
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return setting


@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(key: str, body: SettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    setting.value = body.value
    db.commit()
    db.refresh(setting)
    invalidate_settings_cache()
    return setting


# ── Connection Tests ──────────────────────────────────────────────────────────

@router.post("/settings/test/ha", response_model=ConnectionTestResult)
async def test_ha_connection():
    from app.services.home_assistant import ha_client
    result = await ha_client.test_connection()
    return ConnectionTestResult(**result)


@router.post("/settings/test/octopus", response_model=ConnectionTestResult)
async def test_octopus_connection():
    from app.services.octopus_energy import octopus_client
    result = await octopus_client.test_connection()
    return ConnectionTestResult(**result)


@router.post("/settings/test/influx", response_model=ConnectionTestResult)
async def test_influx_connection():
    from app.services.influxdb import influx_client
    result = await influx_client.test_connection()
    return ConnectionTestResult(**result)


# ── Export / Import ───────────────────────────────────────────────────────────

@router.get("/settings/export")
def export_settings(db: Session = Depends(get_db)):
    """Export all settings as JSON."""
    rows = db.query(SystemSetting).all()
    return {row.key: row.value for row in rows}


@router.post("/settings/import")
def import_settings(settings: Dict[str, str], db: Session = Depends(get_db)):
    """Import settings from a JSON dict."""
    updated = 0
    for key, value in settings.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = value
            updated += 1
    db.commit()
    invalidate_settings_cache()
    return {"imported": updated}


# ── System Control ────────────────────────────────────────────────────────────

@router.post("/system/optimize-now")
async def optimize_now():
    """Force an immediate optimization run."""
    from app.core.scheduler import optimization_loop
    await optimization_loop()
    return {"status": "ok", "message": "Optimization triggered"}


@router.post("/system/pause")
def pause_automation():
    """Pause the APScheduler (stops all automation)."""
    from app.core.scheduler import scheduler
    scheduler.pause()
    return {"status": "paused"}


@router.post("/system/resume")
def resume_automation():
    """Resume the APScheduler."""
    from app.core.scheduler import scheduler
    scheduler.resume()
    return {"status": "running"}
