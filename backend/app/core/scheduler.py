"""APScheduler jobs — replaces all Node-RED automation flows.
Every job wraps its body in try/except so HA unavailability never crashes the scheduler."""

import logging
import math
import zoneinfo
from datetime import datetime, timezone
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.settings_cache import get_setting_int, get_setting_float

logger = logging.getLogger(__name__)


def _build_solar_forecast_profile(
    prices,
    solar_now_kw: float,
    solar_forecast_remaining_kwh: Optional[float],
) -> List[float]:
    """Build a per-period solar forecast profile (kW per half-hour slot).

    Strategy:
    - If we have a remaining-today forecast (kWh), distribute it across future
      daylight periods using a half-sine shape peaking at solar_now_kw.
    - If no forecast is available, use solar_now_kw as a constant fallback.

    The half-sine is anchored so that the integral equals solar_forecast_remaining_kwh.
    Periods after sunset (price period start hour >= 20 or < 5) are forced to 0.
    """
    n = len(prices)
    profile = [solar_now_kw] * n  # default: constant

    if solar_forecast_remaining_kwh is None or solar_forecast_remaining_kwh <= 0:
        return profile

    # Identify daylight slots (5:00–20:00 Europe/London local time).
    # DB datetimes are naive UTC; attach UTC tzinfo before converting so that
    # BST (UTC+1, late March–October) is handled correctly.
    _LOCAL_TZ = zoneinfo.ZoneInfo("Europe/London")
    daylight_indices = []
    for i, p in enumerate(prices):
        local_dt = p.valid_from.replace(tzinfo=timezone.utc).astimezone(_LOCAL_TZ)
        hour = local_dt.hour
        if 5 <= hour < 20:
            daylight_indices.append(i)

    if not daylight_indices:
        return profile

    # Half-sine weights over daylight slots.
    # Use (k+1)/(m+1) so that the first and last slots receive a small positive
    # weight rather than exactly 0 (which sin(0) and sin(π) would give).
    m = len(daylight_indices)
    weights = [math.sin(math.pi * (k + 1) / (m + 1)) for k in range(m)]
    weight_sum = sum(weights)

    # Each slot is 0.5 hr; total energy = sum(kW * 0.5)
    # Scale weights so integral = solar_forecast_remaining_kwh
    scale = solar_forecast_remaining_kwh / (weight_sum * 0.5) if weight_sum > 0 else 0

    result = [0.0] * n
    for rank, idx in enumerate(daylight_indices):
        result[idx] = weights[rank] * scale

    return result

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job("interval", minutes=5, id="optimization_loop")
async def optimization_loop():
    """Every 5min: get system state, run LP optimizer, apply to HA, store results."""
    try:
        from app.core.optimizer import OptimizationInput, run_optimization
        from app.core.action_executor import action_executor
        from app.core.settings_cache import get_setting
        from app.database import SessionLocal
        from app.models.optimization import OptimizationResult, SystemState
        from app.models.prices import ElectricityPrice
        from app.services.home_assistant import ha_client
        from app.services.influxdb import influx_client
        from app.websocket.manager import manager

        # Get current system state from HA
        soc = await ha_client.get_battery_soc()
        solar = await ha_client.get_solar_power()
        solar_forecast = await ha_client.get_solar_forecast_today()
        battery_mode = await ha_client.get_battery_mode()
        # Note 1: live BMS charge rate for LP upper-bound cap
        live_charge_rate = await ha_client.get_charge_rate()
        # Live battery voltage for accurate kW→amps conversion
        live_battery_voltage = await ha_client.get_battery_voltage()

        # Get upcoming prices from DB
        # DB stores naive UTC datetimes — use utcnow() (naive) for comparisons
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            prices_rows = (
                db.query(ElectricityPrice)
                .filter(ElectricityPrice.valid_to >= now)
                .order_by(ElectricityPrice.valid_from)
                .limit(96)
                .all()
            )
            current_price = next(
                (p.price_pence for p in prices_rows if p.valid_from <= now <= p.valid_to),
                None,
            )
        finally:
            db.close()

        from app.core.optimizer import PricePeriod
        price_periods = [
            PricePeriod(p.valid_from, p.valid_to, p.price_pence)
            for p in prices_rows
        ]

        # Build per-period solar forecast profile from remaining-today kWh
        solar_profile = _build_solar_forecast_profile(
            prices=price_periods,
            solar_now_kw=solar or 0.0,
            solar_forecast_remaining_kwh=solar_forecast,
        )

        inp = OptimizationInput(
            battery_soc=soc or 50.0,
            solar_power_kw=solar or 0.0,
            prices=price_periods,
            solar_forecast_profile=solar_profile,
            live_charge_rate_kw=live_charge_rate,
            live_battery_voltage_v=live_battery_voltage,
        )

        result = await run_optimization(inp)

        # Apply to HA
        await action_executor.apply_battery(result)

        # Store result in DB
        db = SessionLocal()
        try:
            opt_record = OptimizationResult(
                timestamp=datetime.now(),
                current_soc=soc,
                current_solar_kw=solar,
                current_price_pence=current_price,
                recommended_mode=result.recommended_mode,
                recommended_discharge_current=result.recommended_discharge_current,
                optimization_status=result.optimization_status,
                optimization_time_ms=result.optimization_time_ms,
                objective_value=result.objective_value,
                decision_reason=result.decision_reason,
            )
            db.add(opt_record)

            state_record = SystemState(
                timestamp=datetime.now(),
                battery_soc=soc,
                battery_mode=battery_mode,
                solar_power_kw=solar,
                solar_forecast_today_kwh=solar_forecast,
                current_price_pence=current_price,
            )
            db.add(state_record)
            db.commit()
        finally:
            db.close()

        # Compute price classification from DB thresholds
        price_classification = None
        if current_price is not None:
            neg_thresh = get_setting_float("price_negative_threshold", 0.0)
            cheap_thresh = get_setting_float("price_cheap_threshold", 10.0)
            exp_thresh = get_setting_float("price_expensive_threshold", 25.0)
            if current_price < neg_thresh:
                price_classification = "negative"
            elif current_price < cheap_thresh:
                price_classification = "cheap"
            elif current_price > exp_thresh:
                price_classification = "expensive"
            else:
                price_classification = "normal"

        # Push to WebSocket clients
        await manager.broadcast({
            "type": "optimization_result",
            "data": {
                "battery_soc": soc,
                "battery_mode": battery_mode,
                "solar_power_kw": solar,
                "solar_forecast_today_kwh": solar_forecast,
                "current_price_pence": current_price,
                "price_classification": price_classification,
                "recommended_mode": result.recommended_mode,
                "decision_reason": result.decision_reason,
                "live_charge_rate_kw": live_charge_rate,
                "last_updated": datetime.now().isoformat(),
            },
        })

        # Write to InfluxDB
        influx_client.write_system_state({
            "battery_soc": soc,
            "battery_mode": battery_mode,
            "solar_power_kw": solar,
            "current_price_pence": current_price,
            "live_charge_rate_kw": live_charge_rate,
        })

    except Exception as e:
        logger.error(f"optimization_loop failed: {e}", exc_info=True)


@scheduler.scheduled_job("interval", minutes=30, id="price_refresh")
async def price_refresh():
    """Every 30min: fetch latest Agile prices from Octopus API and store in DB."""
    try:
        from app.database import SessionLocal
        from app.models.prices import ElectricityPrice
        from app.services.octopus_energy import octopus_client
        from app.services.influxdb import influx_client
        from app.websocket.manager import manager

        prices = await octopus_client.fetch_prices()
        if not prices:
            logger.warning("price_refresh: no prices returned from Octopus")
            return

        db = SessionLocal()
        try:
            for p in prices:
                # Upsert: delete existing period then insert
                db.query(ElectricityPrice).filter(
                    ElectricityPrice.valid_from == p["valid_from"]
                ).delete()
                record = ElectricityPrice(
                    valid_from=p["valid_from"],
                    valid_to=p["valid_to"],
                    price_pence=p["price_pence"],
                    classification=p["classification"],
                )
                db.add(record)
            db.commit()
        finally:
            db.close()

        influx_client.write_prices(prices)
        await manager.broadcast({"type": "prices_updated", "data": prices})
        logger.info(f"price_refresh: stored {len(prices)} price periods")

    except Exception as e:
        logger.error(f"price_refresh failed: {e}", exc_info=True)


@scheduler.scheduled_job("interval", minutes=1, id="immersion_evaluation")
async def immersion_evaluation():
    """Every 1min: evaluate immersion rules for each enabled device and apply decisions."""
    try:
        from datetime import datetime
        from app.core.rules_engine import rules_engine, SystemState as RulesState
        from app.core.action_executor import action_executor
        from app.database import SessionLocal
        from app.models.immersion import ImmersionDevice
        from app.models.overrides import ManualOverride
        from app.models.prices import ElectricityPrice
        from app.services.home_assistant import ha_client

        db = SessionLocal()
        try:
            devices = db.query(ImmersionDevice).filter(ImmersionDevice.is_enabled == True).all()
            # DB stores naive UTC datetimes — use utcnow() (naive) for comparisons
            now = datetime.utcnow()

            # Get current price
            current_price_row = (
                db.query(ElectricityPrice)
                .filter(ElectricityPrice.valid_from <= now, ElectricityPrice.valid_to >= now)
                .first()
            )
            current_price = current_price_row.price_pence if current_price_row else None

            soc = await ha_client.get_battery_soc()
            solar = await ha_client.get_solar_power()

            state = RulesState(
                battery_soc=soc,
                solar_power_kw=solar,
                current_price_pence=current_price,
            )

            for device in devices:
                temp = None
                if device.temp_sensor_entity_id:
                    temp = await ha_client.get_temperature(device.temp_sensor_entity_id)

                # Get active override
                active_override = (
                    db.query(ManualOverride)
                    .filter(
                        ManualOverride.immersion_id == device.id,
                        ManualOverride.is_active == True,
                        ManualOverride.expires_at > datetime.now(),
                    )
                    .first()
                )

                decision = rules_engine.evaluate(
                    device=device,
                    state=state,
                    current_temp=temp,
                    active_override=active_override,
                    temp_targets=device.temp_targets,
                    smart_rules=device.smart_rules,
                )

                await action_executor.apply_immersion(device, decision)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"immersion_evaluation failed: {e}", exc_info=True)
