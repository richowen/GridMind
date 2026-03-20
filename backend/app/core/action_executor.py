"""Action executor — applies optimizer and rules engine decisions to Home Assistant.
Only calls HA when state actually changes. Logs every action to system_actions table."""

import logging
from typing import Optional

from app.utils import utcnow

from sqlalchemy.orm import Session

from app.core.rules_engine import ImmersionDecision
from app.core.optimizer import OptimizationOutput
from app.database import SessionLocal
from app.models.actions import SystemAction
from app.services.home_assistant import ha_client
from app.services.influxdb import influx_client

logger = logging.getLogger(__name__)


def _log_action(
    action_type: str,
    entity_id: str,
    old_value: Optional[str],
    new_value: str,
    source: str,
    reason: Optional[str],
    success: bool,
    db: Optional[Session] = None,
) -> None:
    """Write an action record to the system_actions audit log.

    If a db session is provided, uses it (caller is responsible for commit).
    Otherwise opens its own session and commits immediately.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        action = SystemAction(
            timestamp=utcnow(),
            action_type=action_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            source=source,
            reason=reason,
            success=success,
        )
        db.add(action)
        if own_session:
            db.commit()
    except Exception as e:
        logger.error(f"Failed to log action: {e}")
    finally:
        if own_session:
            db.close()


class ActionExecutor:
    """Applies decisions to Home Assistant, only when state changes."""

    async def apply_battery(self, result: OptimizationOutput, db: Optional[Session] = None) -> None:
        """Apply battery optimizer recommendation to HA."""
        from app.core.settings_cache import get_setting

        # Only call HA if mode actually changes
        current_mode = await ha_client.get_battery_mode()
        if current_mode != result.recommended_mode:
            success = await ha_client.set_battery_mode(result.recommended_mode)
            entity_id = get_setting("ha_entity_battery_mode", "select.foxinverter_work_mode")
            _log_action(
                "battery_mode", entity_id,
                current_mode, result.recommended_mode,
                "optimizer", result.decision_reason, success,
                db=db,
            )
            logger.info(f"Battery mode: {current_mode} → {result.recommended_mode} ({result.decision_reason})")

        # Only set discharge current when actively force-discharging.
        # In Self Use and Force Charge modes the inverter manages its own discharge.
        if result.recommended_mode == "Force Discharge":
            entity_id = get_setting("ha_entity_discharge_current", "number.foxinverter_max_discharge_current")
            current_amps = await ha_client.get_state_float(entity_id)
            target_amps = float(result.recommended_discharge_current)
            if current_amps is None or abs((current_amps or 0) - target_amps) > 0.5:
                success = await ha_client.set_discharge_current(result.recommended_discharge_current)
                _log_action(
                    "discharge_current", entity_id,
                    str(current_amps), str(result.recommended_discharge_current),
                    "optimizer", result.decision_reason, success,
                    db=db,
                )

    async def apply_immersion(self, device, decision: ImmersionDecision, db: Optional[Session] = None) -> None:
        """Apply immersion decision to HA. Only acts if state changes.

        After a successful switch command, records last_commanded_state on the device
        so the scheduler can detect future external (non-GridMind) HA state changes.
        """
        current_state = await ha_client.get_switch_state(device.switch_entity_id)

        if current_state != decision.action:
            success = await ha_client.set_switch(device.switch_entity_id, decision.action)
            _log_action(
                "immersion",
                device.switch_entity_id,
                "on" if current_state else "off",
                "on" if decision.action else "off",
                decision.source,
                decision.reason,
                success,
                db=db,
            )
            logger.info(
                f"Immersion {device.name}: {'ON' if decision.action else 'OFF'} "
                f"({decision.source}: {decision.reason})"
            )

            # Write action event to InfluxDB
            influx_client.write_immersion_action(device.name, {
                "action": decision.action,
                "source": decision.source,
                "reason": decision.reason,
            })

            # Record what GridMind last commanded so the scheduler can detect
            # future external HA changes (state differs from last_commanded_state).
            if success:
                device.last_commanded_state = decision.action
                if db is not None:
                    try:
                        db.flush()
                    except Exception as e:
                        logger.warning(f"Could not flush last_commanded_state for {device.name}: {e}")
                else:
                    logger.warning(
                        f"last_commanded_state updated in-memory for {device.name} but no db "
                        "session provided — change will not be persisted to the database."
                    )


action_executor = ActionExecutor()
