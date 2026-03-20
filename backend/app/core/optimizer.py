"""LP battery optimizer using PuLP/CBC.

Fixes vs V2:
  (1) Fixed SEG export price, not % of import
  (2) Configurable constant load assumption

Fixes vs V3:
  (3) Discharge efficiency applied in SOC dynamics (was missing)
  (4) Per-period solar forecast profile supported (falls back to constant if not provided)
  (5) Force Charge threshold is now a configurable setting
  (6) Battery voltage is now a configurable setting (was hardcoded 48V)
  (7) Force Discharge mode added when LP recommends net export in period 0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.core.settings_cache import get_setting_float, get_setting_int

logger = logging.getLogger(__name__)


@dataclass
class PricePeriod:
    valid_from: datetime
    valid_to: datetime
    price_pence: float


@dataclass
class OptimizationInput:
    battery_soc: float
    solar_power_kw: float
    prices: List[PricePeriod]
    # Optional per-period solar forecast (kW per half-hour slot).
    # If provided, must be the same length as prices (or longer).
    # If None or shorter than prices, falls back to solar_power_kw for missing slots.
    solar_forecast_profile: Optional[List[float]] = field(default=None)
    # Live BMS charge rate from sensor.foxinverter_bms_charge_rate (kW).
    # When provided, caps the LP charge upper bound to min(setting_max, live_rate).
    # None means no live cap — setting_max is used as-is.
    live_charge_rate_kw: Optional[float] = field(default=None)
    # Live battery voltage from sensor.foxinverter_invbatvolt (V).
    # When provided, used for kW→amps conversion instead of the static battery_voltage_v setting.
    live_battery_voltage_v: Optional[float] = field(default=None)


@dataclass
class OptimizationOutput:
    recommended_mode: str          # 'Force Charge', 'Force Discharge', or 'Self Use'
    recommended_discharge_current: int
    decision_reason: str
    optimization_status: str       # 'optimal', 'infeasible', 'error', 'no_prices'
    objective_value: Optional[float]
    optimization_time_ms: float


class BatteryOptimizer:
    """LP optimizer for battery charge/discharge scheduling."""

    def optimize(self, inp: OptimizationInput) -> OptimizationOutput:
        """Run LP optimization. Blocking — call via run_in_executor from async context."""
        start = time.time()

        if not inp.prices:
            # Use the same voltage-aware formula as the happy path.
            # battery_voltage_v falls back to 48 V when the live sensor is unavailable.
            _fallback_voltage = (
                inp.live_battery_voltage_v
                if inp.live_battery_voltage_v and inp.live_battery_voltage_v > 10
                else get_setting_float("battery_voltage_v", 48.0)
            )
            _fallback_amps = int(
                get_setting_float("battery_max_discharge_kw", 5.0) * 1000 / _fallback_voltage
            )
            return OptimizationOutput(
                recommended_mode="Self Use",
                recommended_discharge_current=_fallback_amps,
                decision_reason="No price data available — defaulting to Self Use",
                optimization_status="no_prices",
                objective_value=None,
                optimization_time_ms=0,
            )

        try:
            result = self._run_lp(inp)
            result.optimization_time_ms = (time.time() - start) * 1000
            return result
        except Exception as e:
            logger.error(f"LP optimization failed: {e}")
            return OptimizationOutput(
                recommended_mode="Self Use",
                recommended_discharge_current=50,
                decision_reason=f"Optimization error: {e}",
                optimization_status="error",
                objective_value=None,
                optimization_time_ms=(time.time() - start) * 1000,
            )

    def _run_lp(self, inp: OptimizationInput) -> OptimizationOutput:
        """Core LP formulation."""
        import pulp

        # ── Settings ──────────────────────────────────────────────────────────
        battery_capacity    = get_setting_float("battery_capacity_kwh", 10.6)
        max_charge_kw       = get_setting_float("battery_max_charge_kw", 10.5)
        max_discharge_kw    = get_setting_float("battery_max_discharge_kw", 5.0)
        # FIX (3): efficiency applied symmetrically to both charge and discharge
        efficiency          = get_setting_float("battery_efficiency", 0.95)
        min_soc             = get_setting_int("battery_min_soc", 10) / 100.0
        max_soc             = get_setting_int("battery_max_soc", 100) / 100.0
        grid_import_limit   = get_setting_float("grid_import_limit_kw", 15.0)
        grid_export_limit   = get_setting_float("grid_export_limit_kw", 5.0)
        # FIX (1): Fixed SEG export price (not % of import price)
        export_price_pence  = get_setting_float("export_price_pence", 15.0)
        # FIX (2): Configurable constant load assumption
        assumed_load_kw     = get_setting_float("assumed_load_kw", 2.0)
        # FIX (5): Configurable Force Charge decision threshold
        force_charge_threshold_kw = get_setting_float("force_charge_threshold_kw", 0.5)
        # FIX (6): Use live battery voltage when available; fall back to configurable setting
        battery_voltage_v = (
            inp.live_battery_voltage_v
            if inp.live_battery_voltage_v and inp.live_battery_voltage_v > 10
            else get_setting_float("battery_voltage_v", 48.0)
        )

        # Note 1: Cap max_charge_kw by live BMS charge rate if available
        if inp.live_charge_rate_kw is not None and inp.live_charge_rate_kw > 0:
            effective_max_charge_kw = min(max_charge_kw, inp.live_charge_rate_kw)
            logger.debug(
                f"Live BMS charge rate {inp.live_charge_rate_kw:.2f} kW caps "
                f"setting max {max_charge_kw:.2f} kW → effective {effective_max_charge_kw:.2f} kW"
            )
        else:
            effective_max_charge_kw = max_charge_kw

        num_periods = min(len(inp.prices), get_setting_int("optimization_horizon_hours", 24) * 2)
        periods = inp.prices[:num_periods]
        period_prices = [p.price_pence for p in periods]

        # FIX (4): Per-period solar profile — use forecast if provided, else constant
        def _solar_for_period(t: int) -> float:
            if inp.solar_forecast_profile and t < len(inp.solar_forecast_profile):
                return inp.solar_forecast_profile[t]
            return inp.solar_power_kw

        # ── LP problem ────────────────────────────────────────────────────────
        prob = pulp.LpProblem("battery_optimizer", pulp.LpMinimize)

        # Decision variables
        grid_import = [
            pulp.LpVariable(f"import_{t}", lowBound=0, upBound=grid_import_limit)
            for t in range(num_periods)
        ]
        grid_export = [
            pulp.LpVariable(f"export_{t}", lowBound=0, upBound=grid_export_limit)
            for t in range(num_periods)
        ]
        charge = [
            pulp.LpVariable(f"charge_{t}", lowBound=0, upBound=effective_max_charge_kw)
            for t in range(num_periods)
        ]
        discharge = [
            pulp.LpVariable(f"discharge_{t}", lowBound=0, upBound=max_discharge_kw)
            for t in range(num_periods)
        ]
        soc = [
            pulp.LpVariable(
                f"soc_{t}",
                lowBound=min_soc * battery_capacity,
                upBound=max_soc * battery_capacity,
            )
            for t in range(num_periods)
        ]

        # Objective: minimise net cost (FIX 1: fixed export price)
        prob += pulp.lpSum([
            grid_import[t] * period_prices[t] * 0.5   # Import cost (0.5 hr periods)
            - grid_export[t] * export_price_pence * 0.5  # Export revenue (fixed SEG rate)
            for t in range(num_periods)
        ])

        # ── Constraints ───────────────────────────────────────────────────────
        initial_soc = inp.battery_soc / 100.0 * battery_capacity
        for t in range(num_periods):
            solar_t = _solar_for_period(t)

            # Energy balance: load + charge + export = solar + discharge + import
            prob += (
                assumed_load_kw + charge[t] + grid_export[t]
                == solar_t + discharge[t] + grid_import[t]
            )

            # FIX (3): SOC dynamics — discharge efficiency applied (was missing)
            # Charge adds energy at round-trip efficiency; discharge removes raw energy.
            # Using one-way efficiency per direction: sqrt(round_trip) each way.
            # Simpler conservative model: charge * eff, discharge / eff.
            # PuLP does not support dividing an LpVariable by a scalar (no __truediv__).
            # Rewrite discharge / efficiency as discharge * (1 / efficiency).
            inv_eff = 1.0 / efficiency
            if t == 0:
                prob += (
                    soc[t]
                    == initial_soc
                    + charge[t] * efficiency * 0.5
                    - discharge[t] * inv_eff * 0.5
                )
            else:
                prob += (
                    soc[t]
                    == soc[t - 1]
                    + charge[t] * efficiency * 0.5
                    - discharge[t] * inv_eff * 0.5
                )

        # ── Solve ─────────────────────────────────────────────────────────────
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        status = pulp.LpStatus[prob.status]
        if status != "Optimal":
            return OptimizationOutput(
                recommended_mode="Self Use",
                recommended_discharge_current=50,
                decision_reason=f"LP status: {status}",
                optimization_status="infeasible",
                objective_value=None,
                optimization_time_ms=0,
            )

        # ── Determine recommendation from period 0 ────────────────────────────
        charge_0    = pulp.value(charge[0]) or 0.0
        discharge_0 = pulp.value(discharge[0]) or 0.0
        export_0    = pulp.value(grid_export[0]) or 0.0

        # FIX (5): configurable threshold; FIX (7): Force Discharge mode
        if charge_0 >= force_charge_threshold_kw:
            mode = "Force Charge"
            reason = (
                f"LP optimal: charging {charge_0:.2f} kW at {period_prices[0]:.1f}p "
                f"(threshold {force_charge_threshold_kw} kW)"
            )
        # Intentionally reuses force_charge_threshold_kw as the discharge trigger threshold.
        # A separate force_discharge_threshold_kw setting can be added if independent tuning
        # is needed in future.
        elif discharge_0 >= force_charge_threshold_kw and export_0 > 0.05:
            # LP wants to actively discharge to grid — use Force Discharge
            mode = "Force Discharge"
            reason = (
                f"LP optimal: discharging {discharge_0:.2f} kW to grid at {period_prices[0]:.1f}p"
            )
        else:
            mode = "Self Use"
            reason = f"LP optimal: self-use at {period_prices[0]:.1f}p"

        # FIX (6): use configurable battery voltage for current calculation
        max_discharge_amps = int(max_discharge_kw * 1000 / battery_voltage_v)

        return OptimizationOutput(
            recommended_mode=mode,
            recommended_discharge_current=max_discharge_amps,
            decision_reason=reason,
            optimization_status="optimal",
            objective_value=pulp.value(prob.objective),
            optimization_time_ms=0,
        )


async def run_optimization(inp: OptimizationInput) -> OptimizationOutput:
    """Run LP optimization in thread pool to avoid blocking the event loop."""
    optimizer = BatteryOptimizer()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, optimizer.optimize, inp)
