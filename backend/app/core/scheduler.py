"""APScheduler jobs — replaces all Node-RED automation flows.
Every job wraps its body in try/except so HA unavailability never crashes the scheduler."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.settings_cache import get_setting_int

logger = logging.getLogger(__name__)

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

        inp = OptimizationInput(
            battery_soc=soc or 50.0,
            solar_power_kw=solar or 0.0,
            prices=price_periods,
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

        # Push to WebSocket clients
        await manager.broadcast({
            "type": "optimization_result",
            "data": {
                "battery_soc": soc,
                "battery_mode": battery_mode,
                "solar_power_kw": solar,
                "current_price_pence": current_price,
                "recommended_mode": result.recommended_mode,
                "decision_reason": result.decision_reason,
                "last_updated": datetime.now().isoformat(),
            },
        })

        # Write to InfluxDB
        influx_client.write_system_state({
            "battery_soc": soc,
            "battery_mode": battery_mode,
            "solar_power_kw": solar,
            "current_price_pence": current_price,
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
