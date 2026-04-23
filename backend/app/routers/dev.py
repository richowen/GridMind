"""Stateless dev/simulate endpoint — runs LP optimizer and rules engine
with all inputs provided in the request body. No DB, no HA required."""
import math
import time
import logging
from contextlib import contextmanager
from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter
import pulp

import app.core.settings_cache as _sc
from app.core.optimizer import PricePeriod
from app.core.rules_engine import RulesEngine, SystemState as RulesState
from app.schemas.dev import SimRequest, SimResponse, SimPeriodResult, SimImmersionResult

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dev"])

# Solar profile: 48 half-hourly slots (00:00-23:30 UTC+0)
# UK-ish: dawn~slot14 (07:00), dusk~slot38 (19:00), peak~slot26 (13:00)
_DAWN, _DUSK = 14, 38

def _build_solar_slots(profile: str, peak_kw: float, n: int = 48) -> List[float]:
    """Return list of n per-slot solar kW values for the chosen profile."""
    span = _DUSK - _DAWN
    base = []
    for t in range(n):
        if t <= _DAWN or t >= _DUSK:
            base.append(0.0)
        else:
            # sin curve, peak slightly after centre (slot 26)
            x = math.pi * (t - _DAWN) / span
            base.append(math.sin(x))

    if profile == "flat":
        return [peak_kw] * n

    if profile == "sunny":
        return [round(v * peak_kw, 3) for v in base]

    if profile == "cloudy":
        # overall ~25% with small deterministic ripple
        result = []
        for t, v in enumerate(base):
            ripple = 0.05 * math.sin(t * 1.3)
            result.append(round(max(0.0, v * peak_kw * (0.22 + ripple)), 3))
        return result

    if profile == "intermittent":
        # sunny but with deterministic cloud patches every ~5 slots
        result = []
        for t, v in enumerate(base):
            # cloud factor: drop to 0.1 in patches
            phase = math.sin(t * 0.9) * math.cos(t * 0.5)
            cf = 0.1 if phase > 0.6 else (0.5 if phase > 0.2 else 1.0)
            result.append(round(v * peak_kw * cf, 3))
        return result

    # fallback: flat
    return [peak_kw] * n


@contextmanager
def _override_settings(overrides: dict):
    """Temporarily replace the settings cache with caller-supplied values."""
    old_cache = dict(_sc._cache)
    old_time = _sc._cache_time
    _sc._cache = {k: str(v) for k, v in overrides.items()}
    _sc._cache_time = float("inf")
    try:
        yield
    finally:
        _sc._cache = old_cache
        _sc._cache_time = old_time


def _run_sim_lp(req: SimRequest, prices: List[PricePeriod]):
    """Run LP, return (OptOutput, per-period variable dicts)."""
    cap = req.battery_capacity_kwh
    max_c = req.battery_max_charge_kw
    max_d = req.battery_max_discharge_kw
    eff = req.battery_efficiency
    min_soc = req.battery_min_soc / 100.0
    max_soc = req.battery_max_soc / 100.0
    g_imp = req.grid_import_limit_kw
    g_exp = req.grid_export_limit_kw
    export_p = req.export_price_pence
    load = req.assumed_load_kw
    fc_thresh = req.force_charge_threshold_kw
    fd_thresh = req.force_discharge_threshold_kw
    fd_exp_min = req.force_discharge_export_min_kw

    if req.live_charge_rate_kw and req.live_charge_rate_kw > 0:
        max_c = min(max_c, req.live_charge_rate_kw)

    n = min(len(prices), req.optimization_horizon_hours * 2)
    periods = prices[:n]
    pvals = [p.price_pence for p in periods]

    # Per-slot solar generation
    peak_kw = req.solar_power_kw * req.solar_scale
    solar_slots = _build_solar_slots(req.solar_profile, peak_kw, 48)[:n]

    prob = pulp.LpProblem("sim", pulp.LpMinimize)
    gi = [pulp.LpVariable(f"gi_{t}", 0, g_imp) for t in range(n)]
    ge = [pulp.LpVariable(f"ge_{t}", 0, g_exp) for t in range(n)]
    ch = [pulp.LpVariable(f"ch_{t}", 0, max_c) for t in range(n)]
    di = [pulp.LpVariable(f"di_{t}", 0, max_d) for t in range(n)]
    soc = [pulp.LpVariable(f"soc_{t}", min_soc*cap, max_soc*cap) for t in range(n)]

    prob += pulp.lpSum(
        gi[t]*pvals[t]*0.5 - ge[t]*export_p*0.5 for t in range(n)
    )

    init_soc = req.battery_soc / 100.0 * cap
    inv_eff = 1.0 / eff
    for t in range(n):
        prob += load + ch[t] + ge[t] == solar_slots[t] + di[t] + gi[t]
        prev = init_soc if t == 0 else soc[t-1]
        prob += soc[t] == prev + ch[t]*eff*0.5 - di[t]*inv_eff*0.5

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    status = pulp.LpStatus[prob.status]

    period_results = []
    for t in range(n):
        soc_kwh = pulp.value(soc[t]) or 0.0
        period_results.append(SimPeriodResult(
            slot=t,
            valid_from=periods[t].valid_from.isoformat() + "Z",
            price_pence=pvals[t],
            solar_kw=solar_slots[t],
            charge_kw=round(pulp.value(ch[t]) or 0.0, 3),
            discharge_kw=round(pulp.value(di[t]) or 0.0, 3),
            grid_import_kw=round(pulp.value(gi[t]) or 0.0, 3),
            grid_export_kw=round(pulp.value(ge[t]) or 0.0, 3),
            soc_kwh=round(soc_kwh, 3),
            soc_pct=round(soc_kwh / cap * 100, 1) if cap > 0 else 0.0,
        ))

    if status != "Optimal":
        return "Self Use", "LP infeasible", "infeasible", None, period_results

    c0 = pulp.value(ch[0]) or 0.0
    d0 = pulp.value(di[0]) or 0.0
    e0 = pulp.value(ge[0]) or 0.0
    obj = pulp.value(prob.objective)

    if c0 >= fc_thresh:
        mode = "Force Charge"
        reason = f"LP: charging {c0:.2f}kW at {pvals[0]:.1f}p (thresh {fc_thresh}kW)"
    elif d0 >= fd_thresh and e0 > fd_exp_min:
        mode = "Force Discharge"
        reason = f"LP: discharging {d0:.2f}kW to grid at {pvals[0]:.1f}p"
    else:
        mode = "Self Use"
        reason = f"LP: self-use at {pvals[0]:.1f}p"

    return mode, reason, "optimal", obj, period_results


def _run_immersion_sim(req: SimRequest) -> Optional[SimImmersionResult]:
    if not req.immersion:
        return None

    from datetime import time as dtime
    from unittest.mock import MagicMock

    imm = req.immersion
    state = RulesState(
        battery_soc=imm.battery_soc,
        solar_power_kw=imm.solar_power_kw,
        current_price_pence=imm.current_price_pence,
    )

    rules = []
    for r in imm.rules:
        mock = MagicMock()
        mock.is_enabled = r.is_enabled
        mock.priority = r.priority
        mock.action = r.action
        mock.rule_name = r.rule_name
        mock.logic_operator = r.logic_operator
        mock.price_enabled = r.price_enabled
        mock.price_operator = r.price_operator
        mock.price_threshold_pence = r.price_threshold_pence
        mock.soc_enabled = r.soc_enabled
        mock.soc_operator = r.soc_operator
        mock.soc_threshold_percent = r.soc_threshold_percent
        mock.solar_enabled = r.solar_enabled
        mock.solar_operator = r.solar_operator
        mock.solar_threshold_kw = r.solar_threshold_kw
        mock.temp_enabled = r.temp_enabled
        mock.temp_operator = r.temp_operator
        mock.temp_threshold_c = r.temp_threshold_c
        mock.time_enabled = r.time_enabled
        try:
            h, m = r.time_start.split(":")
            mock.time_start = dtime(int(h), int(m))
            h2, m2 = r.time_end.split(":")
            mock.time_end = dtime(int(h2), int(m2))
        except Exception:
            mock.time_start = dtime(0, 0)
            mock.time_end = dtime(23, 59)
        rules.append(mock)

    device = MagicMock()
    engine = RulesEngine()
    decision = engine.evaluate(
        device=device,
        state=state,
        current_temp=imm.current_temp_c,
        smart_rules=rules,
    )
    return SimImmersionResult(action=decision.action, source=decision.source, reason=decision.reason)


@router.get("/dev/snapshot")
def snapshot(db=None):
    """Return current system state + settings + 24h prices from DB.
    Used by the dev simulator 'Load Snapshot' button. No HA required."""
    from app.database import SessionLocal
    from app.models.optimization import OptimizationResult
    from app.models.prices import ElectricityPrice
    from app.core.settings_cache import get_settings
    from app.utils import utcnow

    db = SessionLocal()
    try:
        now = utcnow()
        latest = (
            db.query(OptimizationResult)
            .order_by(OptimizationResult.timestamp.desc())
            .first()
        )
        prices_rows = (
            db.query(ElectricityPrice)
            .filter(ElectricityPrice.valid_to >= now)
            .order_by(ElectricityPrice.valid_from)
            .limit(48)
            .all()
        )
        settings = get_settings()
        soc = float(latest.current_soc) if latest and latest.current_soc is not None else 50.0
        solar = float(latest.current_solar_kw) if latest and latest.current_solar_kw is not None else 0.0
        prices = [
            {"valid_from": p.valid_from.isoformat() + "Z", "price_pence": float(p.price_pence)}
            for p in prices_rows
        ]
    finally:
        db.close()

    def _f(key, default):
        try: return float(settings.get(key, default))
        except: return float(default)
    def _i(key, default):
        try: return int(float(settings.get(key, default)))
        except: return int(default)

    return {
        "battery_soc": soc,
        "solar_power_kw": solar,
        "battery_capacity_kwh": _f("battery_capacity_kwh", 20.0),
        "battery_max_charge_kw": _f("battery_max_charge_kw", 10.5),
        "battery_max_discharge_kw": _f("battery_max_discharge_kw", 10.5),
        "battery_efficiency": _f("battery_efficiency", 0.95),
        "battery_min_soc": _i("battery_min_soc", 10),
        "battery_max_soc": _i("battery_max_soc", 100),
        "battery_voltage_v": _f("battery_voltage_v", 48.0),
        "grid_import_limit_kw": _f("grid_import_limit_kw", 15.0),
        "grid_export_limit_kw": _f("grid_export_limit_kw", 5.0),
        "export_price_pence": _f("export_price_pence", 15.0),
        "assumed_load_kw": _f("assumed_load_kw", 2.0),
        "force_charge_threshold_kw": _f("force_charge_threshold_kw", 0.5),
        "force_discharge_threshold_kw": _f("force_discharge_threshold_kw", 0.5),
        "force_discharge_export_min_kw": _f("force_discharge_export_min_kw", 0.05),
        "optimization_horizon_hours": _i("optimization_horizon_hours", 24),
        "prices": prices,
    }


@router.post("/dev/simulate", response_model=SimResponse)
def simulate(req: SimRequest):
    """Run LP optimizer + optional rules engine with caller-supplied inputs.
    No database or Home Assistant connection required."""
    settings_override = {
        "battery_capacity_kwh": req.battery_capacity_kwh,
        "battery_max_charge_kw": req.battery_max_charge_kw,
        "battery_max_discharge_kw": req.battery_max_discharge_kw,
        "battery_efficiency": req.battery_efficiency,
        "battery_min_soc": req.battery_min_soc,
        "battery_max_soc": req.battery_max_soc,
        "battery_voltage_v": req.battery_voltage_v,
        "grid_import_limit_kw": req.grid_import_limit_kw,
        "grid_export_limit_kw": req.grid_export_limit_kw,
        "export_price_pence": req.export_price_pence,
        "assumed_load_kw": req.assumed_load_kw,
        "force_charge_threshold_kw": req.force_charge_threshold_kw,
        "force_discharge_threshold_kw": req.force_discharge_threshold_kw,
        "force_discharge_export_min_kw": req.force_discharge_export_min_kw,
        "optimization_horizon_hours": req.optimization_horizon_hours,
    }

    t0 = time.time()
    # Use live voltage if supplied and valid, else fall back to configured setting
    _volt = (req.live_battery_voltage_v or 0) if (req.live_battery_voltage_v and req.live_battery_voltage_v > 10) else req.battery_voltage_v
    max_d_amps = int(req.battery_max_discharge_kw * 1000 / _volt)

    if not req.prices:
        return SimResponse(
            recommended_mode="Self Use",
            decision_reason="No prices provided",
            optimization_status="no_prices",
            objective_value=None,
            optimization_time_ms=0,
            recommended_discharge_current=max_d_amps,
            periods=[],
            immersion=_run_immersion_sim(req),
        )

    prices = []
    for i, p in enumerate(req.prices):
        valid_from = p.valid_from.replace(tzinfo=None)
        valid_to = valid_from + timedelta(minutes=30)
        prices.append(PricePeriod(valid_from=valid_from, valid_to=valid_to, price_pence=p.price_pence))

    with _override_settings(settings_override):
        mode, reason, status, obj, periods = _run_sim_lp(req, prices)

    elapsed_ms = (time.time() - t0) * 1000

    return SimResponse(
        recommended_mode=mode,
        decision_reason=reason,
        optimization_status=status,
        objective_value=round(obj, 4) if obj is not None else None,
        optimization_time_ms=round(elapsed_ms, 1),
        recommended_discharge_current=max_d_amps,
        periods=periods,
        immersion=_run_immersion_sim(req),
    )
