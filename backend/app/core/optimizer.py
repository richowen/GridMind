"""LP battery optimizer using PuLP/CBC.
Key fixes vs V2: (1) fixed SEG export price, not % of import; (2) configurable constant load assumption."""

import asyncio
import logging
import time
from dataclasses import dataclass
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


@dataclass
class OptimizationOutput:
    recommended_mode: str          # 'Force Charge' or 'Self Use'
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
            return OptimizationOutput(
                recommended_mode="Self Use",
                recommended_discharge_current=get_setting_int("battery_max_discharge_kw", 5) * 10,
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

        # Settings
        battery_capacity = get_setting_float("battery_capacity_kwh", 10.6)
        max_charge_kw = get_setting_float("battery_max_charge_kw", 10.5)
        max_discharge_kw = get_setting_float("battery_max_discharge_kw", 5.0)
        efficiency = get_setting_float("battery_efficiency", 0.95)
        min_soc = get_setting_int("battery_min_soc", 10) / 100.0
        max_soc = get_setting_int("battery_max_soc", 100) / 100.0
        grid_import_limit = get_setting_float("grid_import_limit_kw", 15.0)
        grid_export_limit = get_setting_float("grid_export_limit_kw", 5.0)
        # FIX 1: Fixed SEG export price (not % of import price)
        export_price_pence = get_setting_float("export_price_pence", 15.0)
        # FIX 2: Configurable constant load assumption
        assumed_load_kw = get_setting_float("assumed_load_kw", 2.0)

        num_periods = min(len(inp.prices), get_setting_int("optimization_horizon_hours", 24) * 2)
        periods = inp.prices[:num_periods]
        period_prices = [p.price_pence for p in periods]

        prob = pulp.LpProblem("battery_optimizer", pulp.LpMinimize)

        # Decision variables
        grid_import = [pulp.LpVariable(f"import_{t}", lowBound=0, upBound=grid_import_limit) for t in range(num_periods)]
        grid_export = [pulp.LpVariable(f"export_{t}", lowBound=0, upBound=grid_export_limit) for t in range(num_periods)]
        charge = [pulp.LpVariable(f"charge_{t}", lowBound=0, upBound=max_charge_kw) for t in range(num_periods)]
        discharge = [pulp.LpVariable(f"discharge_{t}", lowBound=0, upBound=max_discharge_kw) for t in range(num_periods)]
        soc = [pulp.LpVariable(f"soc_{t}", lowBound=min_soc * battery_capacity, upBound=max_soc * battery_capacity) for t in range(num_periods)]

        # Objective: minimize cost (FIX 1: fixed export price)
        prob += pulp.lpSum([
            grid_import[t] * period_prices[t] * 0.5 -   # Import cost (0.5hr periods)
            grid_export[t] * export_price_pence * 0.5    # Export revenue (fixed SEG rate)
            for t in range(num_periods)
        ])

        # Constraints
        initial_soc = inp.battery_soc / 100.0 * battery_capacity
        for t in range(num_periods):
            # Energy balance: load + charge + export = solar + discharge + import
            # FIX 2: constant load assumption
            prob += (assumed_load_kw + charge[t] + grid_export[t] ==
                     inp.solar_power_kw + discharge[t] + grid_import[t])

            # SOC dynamics
            if t == 0:
                prob += soc[t] == initial_soc + charge[t] * efficiency * 0.5 - discharge[t] * 0.5
            else:
                prob += soc[t] == soc[t-1] + charge[t] * efficiency * 0.5 - discharge[t] * 0.5

        # Solve
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

        # Determine recommendation from first period
        charge_0 = pulp.value(charge[0]) or 0
        mode = "Force Charge" if charge_0 > 0.1 else "Self Use"
        max_discharge_amps = int(max_discharge_kw * 1000 / 48)  # Approx for 48V system
        reason = f"LP optimal: {'charging' if mode == 'Force Charge' else 'self-use'} at {period_prices[0]:.1f}p"

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
