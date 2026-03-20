"""Configurable immersion rules engine. Evaluates DB-stored rules in priority order.
Priority: 1=Manual Override, 2=Temperature Target, 3+=Smart Rules, default=OFF."""

import logging
from dataclasses import dataclass
from datetime import datetime, time
from operator import eq, ge, gt, le, lt
from typing import Optional

logger = logging.getLogger(__name__)

OPS = {"<": lt, "<=": le, ">": gt, ">=": ge, "==": eq}


@dataclass
class SystemState:
    battery_soc: Optional[float]
    solar_power_kw: Optional[float]
    current_price_pence: Optional[float]


@dataclass
class ImmersionDecision:
    action: bool           # True = ON, False = OFF
    source: str            # 'manual_override', 'temperature_target', 'smart_rule', 'default'
    reason: str


class RulesEngine:
    """Evaluates all rules for an immersion device and returns a decision."""

    def evaluate(
        self,
        device,
        state: SystemState,
        current_temp: Optional[float],
        active_override=None,
        temp_targets=None,
        smart_rules=None,
    ) -> ImmersionDecision:
        """Evaluate rules in priority order. Returns first matching decision."""

        # PRIORITY 1: Manual Override (always wins)
        if active_override:
            # expires_at is stored as naive UTC — compare against utcnow()
            remaining = int((active_override.expires_at - datetime.utcnow()).total_seconds() / 60)
            return ImmersionDecision(
                action=active_override.desired_state,
                source="manual_override",
                reason=f"Manual override active ({remaining}min remaining)",
            )

        # PRIORITY 2: Temperature Targets
        for target in (temp_targets or []):
            if not target.is_enabled:
                continue
            if self._temp_target_requires_heating(target, current_temp):
                return ImmersionDecision(
                    action=True,
                    source="temperature_target",
                    reason=f"Need {target.target_temp_c}°C by {target.target_time}",
                )

        # PRIORITY 3+: Smart Rules (ordered by priority)
        for rule in sorted(smart_rules or [], key=lambda r: r.priority):
            if not rule.is_enabled:
                continue
            if self._rule_matches(rule, state, current_temp):
                return ImmersionDecision(
                    action=(rule.action == "ON"),
                    source="smart_rule",
                    reason=rule.rule_name,
                )

        # DEFAULT: Off
        return ImmersionDecision(action=False, source="default", reason="No rules matched")

    def _rule_matches(self, rule, state: SystemState, device_temp: Optional[float]) -> bool:
        """Evaluate all enabled conditions using AND/OR logic."""
        conditions = []

        if rule.price_enabled and state.current_price_pence is not None:
            conditions.append(self._compare(state.current_price_pence, rule.price_operator, rule.price_threshold_pence))
        if rule.soc_enabled and state.battery_soc is not None:
            conditions.append(self._compare(state.battery_soc, rule.soc_operator, rule.soc_threshold_percent))
        if rule.solar_enabled and state.solar_power_kw is not None:
            conditions.append(self._compare(state.solar_power_kw, rule.solar_operator, rule.solar_threshold_kw))
        if rule.temp_enabled and device_temp is not None:
            conditions.append(self._compare(device_temp, rule.temp_operator, rule.temp_threshold_c))
        if rule.time_enabled:
            conditions.append(self._in_time_window(rule.time_start, rule.time_end))

        if not conditions:
            return False

        return all(conditions) if rule.logic_operator == "AND" else any(conditions)

    def _temp_target_requires_heating(self, target, current_temp: Optional[float]) -> bool:
        """Returns True if heating must start now to reach target_temp by target_time."""
        if current_temp is None or current_temp >= target.target_temp_c:
            return False

        # Use local time for day-of-week and time-of-day comparisons (these are user-facing schedules)
        now = datetime.now()
        today_weekday = now.weekday()
        target_days = [int(d) for d in target.days_of_week.split(",")]
        if today_weekday not in target_days:
            return False

        target_dt = now.replace(
            hour=target.target_time.hour,
            minute=target.target_time.minute,
            second=0,
            microsecond=0,
        )
        if target_dt <= now:
            return False

        hours_until_target = (target_dt - now).total_seconds() / 3600
        temp_deficit = target.target_temp_c - current_temp
        hours_needed = temp_deficit / target.heating_rate_c_per_hour
        buffer_hours = target.buffer_minutes / 60

        return hours_until_target <= (hours_needed + buffer_hours)

    def _compare(self, value: float, operator: str, threshold: float) -> bool:
        op_fn = OPS.get(operator)
        if op_fn is None:
            logger.warning(f"Unknown operator: {operator}")
            return False
        return op_fn(value, threshold)

    def _in_time_window(self, start: time, end: time) -> bool:
        # Use local time for time-window comparisons (user-facing schedules)
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end  # Crosses midnight


rules_engine = RulesEngine()
