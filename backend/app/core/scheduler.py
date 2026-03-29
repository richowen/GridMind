"""APScheduler jobs — replaces all Node-RED automation flows.
Every job wraps its body in try/except so HA unavailability never crashes the scheduler.

Scheduler intervals are read from DB settings at startup:
  - optimization_interval_minutes (default 5)
  - price_refresh_interval_minutes (default 30)
"""

import logging
import math
import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from app.utils import utcnow

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.settings_cache import get_setting_int

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


def _build_scheduler() -> AsyncIOScheduler:
    """Build the APScheduler instance with intervals read from DB settings.

    Falls back to hardcoded defaults if settings are not yet available
    (e.g. on first boot before migrations run).
    """
    try:
        opt_interval = get_setting_int("optimization_interval_minutes", 5)
        price_interval = get_setting_int("price_refresh_interval_minutes", 30)
    except Exception as e:
        logger.warning(
            f"Could not read scheduler intervals from DB (using defaults 5/30 min): {e}"
        )
        opt_interval = 5
        price_interval = 30

    logger.info(
        f"Scheduler intervals: optimization={opt_interval}min, price_refresh={price_interval}min"
    )

    sched = AsyncIOScheduler()
    sched.add_job(optimization_loop, "interval", minutes=opt_interval, id="optimization_loop")
    sched.add_job(price_refresh, "interval", minutes=price_interval, id="price_refresh")
    sched.add_job(immersion_evaluation, "interval", minutes=1, id="immersion_evaluation")
    return sched


async def optimization_loop():
    """Every N min: get system state, run LP optimizer, apply to HA, store results."""
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
        solar_forecast_today = await ha_client.get_solar_forecast_today()
        solar_forecast_1hr = await ha_client.get_solar_forecast_1hr()
        battery_mode = await ha_client.get_battery_mode()
        # Note 1: live BMS charge rate for LP upper-bound cap
        live_charge_rate = await ha_client.get_charge_rate()
        # Live battery voltage for accurate kW→amps conversion
        live_battery_voltage = await ha_client.get_battery_voltage()

        # Single DB session for the entire optimization cycle
        db = SessionLocal()
        try:
            # DB stores naive UTC datetimes — use utcnow() (naive) for comparisons
            now = utcnow()
            prices_rows = (
                db.query(ElectricityPrice)
                .filter(ElectricityPrice.valid_to >= now)
                .order_by(ElectricityPrice.valid_from)
                .limit(96)
                .all()
            )
            current_price_row = next(
                (p for p in prices_rows if p.valid_from <= now <= p.valid_to),
                None,
            )
            current_price = current_price_row.price_pence if current_price_row else None
            # DIAGNOSTIC: log the UTC time and matched price slot so we can verify
            # the optimizer is using the correct half-hour period (not off by 1hr due to BST).
            if current_price_row:
                logger.info(
                    f"[DIAG] optimization_loop: now={now.isoformat()}Z (UTC), "
                    f"matched slot valid_from={current_price_row.valid_from.isoformat()}Z "
                    f"valid_to={current_price_row.valid_to.isoformat()}Z "
                    f"price={current_price:.2f}p"
                )
            else:
                logger.warning(
                    f"[DIAG] optimization_loop: now={now.isoformat()}Z (UTC), "
                    f"NO matching price slot found. "
                    f"First available slot: "
                    f"{prices_rows[0].valid_from.isoformat() if prices_rows else 'none'}"
                )

            from app.core.optimizer import PricePeriod
            price_periods = [
                PricePeriod(p.valid_from, p.valid_to, p.price_pence)
                for p in prices_rows
            ]

            # Build per-period solar forecast profile from remaining-today kWh
            solar_profile = _build_solar_forecast_profile(
                prices=price_periods,
                solar_now_kw=solar or 0.0,
                solar_forecast_remaining_kwh=solar_forecast_today,
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

            # Apply to HA — pass db so action logs share this session
            await action_executor.apply_battery(result, db=db)

            # Compute next scheduled run time for next_action_time field
            opt_interval_min = get_setting_int("optimization_interval_minutes", 5)
            next_action_time = utcnow() + timedelta(minutes=opt_interval_min)

            # Store result in DB (same session)
            opt_record = OptimizationResult(
                timestamp=utcnow(),
                current_soc=soc,
                current_solar_kw=solar,
                current_price_pence=current_price,
                recommended_mode=result.recommended_mode,
                recommended_discharge_current=result.recommended_discharge_current,
                optimization_status=result.optimization_status,
                optimization_time_ms=result.optimization_time_ms,
                objective_value=result.objective_value,
                decision_reason=result.decision_reason,
                next_action_time=next_action_time,
            )
            db.add(opt_record)

            state_record = SystemState(
                timestamp=utcnow(),
                battery_soc=soc,
                battery_mode=battery_mode,
                solar_power_kw=solar,
                solar_forecast_today_kwh=solar_forecast_today,
                solar_forecast_next_hour_kw=solar_forecast_1hr,
                current_price_pence=current_price,
            )
            db.add(state_record)
            db.commit()

            # Compute price classification while the session is still open —
            # prices_rows are ORM objects that require an active session for
            # attribute access (lazy loading). Must run before db.close().
            from app.services.octopus_energy import get_current_price_classification
            from app.core.settings_cache import get_settings as _get_all_settings
            price_classification = get_current_price_classification(
                price_rows=prices_rows,
                now=now,
                settings=_get_all_settings(),
            )

        finally:
            db.close()

        # Push to WebSocket clients
        await manager.broadcast({
            "type": "optimization_result",
            "data": {
                "battery_soc": soc,
                "battery_mode": battery_mode,
                "solar_power_kw": solar,
                "solar_forecast_today_kwh": solar_forecast_today,
                "solar_forecast_next_hour_kw": solar_forecast_1hr,
                "current_price_pence": current_price,
                "price_classification": price_classification,
                "recommended_mode": result.recommended_mode,
                "decision_reason": result.decision_reason,
                "live_charge_rate_kw": live_charge_rate,
                "last_updated": utcnow().isoformat() + "Z",
            },
        })

        # Write to InfluxDB
        influx_client.write_system_state({
            "battery_soc": soc,
            "battery_mode": battery_mode,
            "solar_power_kw": solar,
            "current_price_pence": current_price,
            "live_charge_rate_kw": live_charge_rate,
            "solar_forecast_today_kwh": solar_forecast_today,
            "solar_forecast_next_hour_kw": solar_forecast_1hr,
        })

    except Exception as e:
        logger.error(f"optimization_loop failed: {e}", exc_info=True)


async def price_refresh():
    """Every N min: fetch latest Agile prices from Octopus API and store in DB."""
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
        # Serialise datetime objects to UTC ISO strings with 'Z' suffix before broadcasting
        # so the frontend can parse them correctly as UTC (not local time).
        prices_serialised = [
            {
                **p,
                "valid_from": p["valid_from"].isoformat() + "Z",
                "valid_to": p["valid_to"].isoformat() + "Z",
            }
            for p in prices
        ]
        await manager.broadcast({"type": "prices_updated", "data": prices_serialised})
        logger.info(f"price_refresh: stored {len(prices)} price periods")

    except Exception as e:
        logger.error(f"price_refresh failed: {e}", exc_info=True)


async def immersion_evaluation():
    """Every 1min: evaluate immersion rules for each enabled device and apply decisions.

    External change detection: if the current HA switch state differs from the last
    state GridMind commanded (last_commanded_state), and no manual override is active,
    GridMind infers the switch was changed externally (e.g. via the HA dashboard) and
    auto-creates a ManualOverride so it does not immediately revert the change.
    """
    try:
        from app.core.rules_engine import rules_engine, SystemState as RulesState
        from app.core.action_executor import action_executor
        from app.core.settings_cache import get_setting_int
        from app.database import SessionLocal
        from app.models.immersion import ImmersionDevice
        from app.models.overrides import ManualOverride
        from app.models.prices import ElectricityPrice
        from app.services.home_assistant import ha_client
        from app.services.influxdb import influx_client
        from app.websocket.manager import manager

        db = SessionLocal()
        try:
            devices = db.query(ImmersionDevice).filter(ImmersionDevice.is_enabled == True).all()
            # DB stores naive UTC datetimes — use utcnow() (naive) for comparisons
            now = utcnow()

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

                # Read current HA switch state once — reused for detection and InfluxDB snapshot
                current_switch_state = await ha_client.get_switch_state(device.switch_entity_id)

                # Get active override — compare expires_at (naive UTC) against pre-computed now
                active_override = (
                    db.query(ManualOverride)
                    .filter(
                        ManualOverride.immersion_id == device.id,
                        ManualOverride.is_active == True,
                        ManualOverride.expires_at > now,
                    )
                    .first()
                )

                # ── External change detection ─────────────────────────────────────────
                # Two cases to handle:
                #
                # Case A — No active override: if the switch state differs from what
                #   GridMind last commanded, the user changed it externally. Auto-create
                #   an override so GridMind doesn't immediately revert the change.
                #   Skip when last_commanded_state is NULL (first boot / never commanded).
                #
                # Case B — Active override exists but switch state contradicts it: the
                #   user manually changed the switch *during* an active override (e.g.
                #   turned it OFF while a "keep ON" override was running). Clear the
                #   override so GridMind doesn't fight the user by turning it back on.
                #   Update last_commanded_state to match so the next cycle is clean.
                # ─────────────────────────────────────────────────────────────────────

                if (
                    active_override is not None
                    and current_switch_state is not None
                    and current_switch_state != active_override.desired_state
                ):
                    # Case B: user changed switch against an active override — clear it.
                    state_label = "ON" if current_switch_state else "OFF"
                    logger.info(
                        f"Switch state for {device.name} contradicts active override "
                        f"(override wants {'ON' if active_override.desired_state else 'OFF'}, "
                        f"switch is {state_label}). Clearing override — user wins."
                    )
                    db.query(ManualOverride).filter(
                        ManualOverride.immersion_id == device.id,
                        ManualOverride.is_active == True,
                    ).update({"is_active": False, "cleared_at": now, "cleared_by": "ha_external_contradiction"})
                    device.last_commanded_state = current_switch_state
                    try:
                        db.flush()
                    except Exception as flush_err:
                        logger.warning(
                            f"Could not flush override clear for {device.name}: {flush_err}. "
                            "Skipping this device for this cycle."
                        )
                        db.rollback()
                        continue
                    # Override is now cleared — let normal rule evaluation run this cycle.
                    active_override = None

                elif (
                    active_override is None
                    and device.last_commanded_state is not None
                    and current_switch_state is not None
                    and current_switch_state != device.last_commanded_state
                ):
                    # Case A: no override, switch changed externally — auto-create override.
                    auto_duration = get_setting_int("manual_override_auto_duration_minutes", 120)
                    state_label = "ON" if current_switch_state else "OFF"
                    logger.info(
                        f"External HA change detected for {device.name}: "
                        f"switch is {state_label} but GridMind last commanded "
                        f"{'ON' if device.last_commanded_state else 'OFF'}. "
                        f"Auto-creating {auto_duration}min override."
                    )

                    # Clear any stale (expired) overrides for this device first
                    db.query(ManualOverride).filter(
                        ManualOverride.immersion_id == device.id,
                        ManualOverride.is_active == True,
                    ).update({"is_active": False, "cleared_at": now, "cleared_by": "auto_detection"})

                    active_override = ManualOverride(
                        immersion_id=device.id,
                        immersion_name=device.name,
                        is_active=True,
                        desired_state=current_switch_state,
                        source="ha_external",
                        expires_at=now + timedelta(minutes=auto_duration),
                    )
                    db.add(active_override)

                    # Update last_commanded_state immediately so the next evaluation
                    # cycle does not re-detect the same change as another external event.
                    device.last_commanded_state = current_switch_state
                    try:
                        db.flush()
                    except Exception as flush_err:
                        logger.warning(
                            f"Could not flush auto-override for {device.name}: {flush_err}. "
                            "Skipping this device for this cycle."
                        )
                        db.rollback()
                        continue

                    # Notify connected frontend clients in real-time
                    await manager.broadcast({
                        "type": "manual_override_detected",
                        "data": {
                            "immersion_id": device.id,
                            "immersion_name": device.name,
                            "desired_state": current_switch_state,
                            "source": "ha_external",
                            "duration_minutes": auto_duration,
                            "expires_at": active_override.expires_at.isoformat() + "Z",
                            "message": (
                                f"{device.display_name} was turned {state_label} manually in "
                                f"Home Assistant — auto-override created for {auto_duration} minutes."
                            ),
                        },
                    })
                # ─────────────────────────────────────────────────────────────────────

                decision = rules_engine.evaluate(
                    device=device,
                    state=state,
                    current_temp=temp,
                    active_override=active_override,
                    temp_targets=device.temp_targets,
                    smart_rules=device.smart_rules,
                )

                await action_executor.apply_immersion(device, decision, db=db)

                # Write per-device immersion state snapshot to InfluxDB.
                # Use the decision outcome as the post-action state rather than
                # current_switch_state (which was fetched before apply_immersion ran
                # and may now be stale if GridMind just changed the switch).
                post_action_state = (
                    decision.action
                    if decision.action is not None
                    else current_switch_state
                )
                influx_client.write_immersion_state(
                    device_name=device.name,
                    is_on=bool(post_action_state),
                    temp_c=temp,
                )

            # Commit any action log entries and override records added during this cycle
            db.commit()

        finally:
            db.close()

    except Exception as e:
        logger.error(f"immersion_evaluation failed: {e}", exc_info=True)


# Build scheduler with DB-configured intervals.
# _build_scheduler() is called at module import time; settings_cache will load
# from DB on first access (or fall back to defaults if DB is not yet ready).
scheduler = _build_scheduler()
