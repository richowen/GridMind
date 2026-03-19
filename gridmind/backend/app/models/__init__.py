"""SQLAlchemy ORM models package. Import all models here so Alembic can detect them."""

from app.models.prices import ElectricityPrice
from app.models.optimization import OptimizationResult, SystemState
from app.models.immersion import ImmersionDevice, ImmersionSmartRule, TemperatureTarget
from app.models.overrides import ManualOverride
from app.models.actions import SystemAction
from app.models.settings import SystemSetting

__all__ = [
    "ElectricityPrice",
    "OptimizationResult",
    "SystemState",
    "ImmersionDevice",
    "ImmersionSmartRule",
    "TemperatureTarget",
    "ManualOverride",
    "SystemAction",
    "SystemSetting",
]
