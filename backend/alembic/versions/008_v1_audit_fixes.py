"""008 — V1 audit fixes: remove dead columns, add new settings.

Drops:
- system_states.immersion_main_on  (hardcoded device column — use InfluxDB immersion_states instead)
- system_states.immersion_lucy_on  (hardcoded device column — use InfluxDB immersion_states instead)
- system_states.battery_discharge_current  (never written by scheduler)

Keeps (now populated):
- system_states.solar_forecast_next_hour_kw  (now written from ha_entity_solar_forecast_1hr)
- optimization_results.next_action_time  (now written with next scheduled run time)

Removes dead settings:
- octopus_region  (tariff code already encodes region; not used in URL construction)

Adds new settings:
- force_discharge_threshold_kw  (independent threshold for Force Discharge mode)
- force_discharge_export_min_kw  (min export guard for Force Discharge)

Revision ID: 008
Revises: 007
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ── Drop dead columns from system_states ──────────────────────────────────
    existing_cols = {col["name"] for col in inspector.get_columns("system_states")}

    with op.batch_alter_table("system_states") as batch_op:
        if "immersion_main_on" in existing_cols:
            batch_op.drop_column("immersion_main_on")
        if "immersion_lucy_on" in existing_cols:
            batch_op.drop_column("immersion_lucy_on")
        if "battery_discharge_current" in existing_cols:
            batch_op.drop_column("battery_discharge_current")

    # ── Remove dead settings ──────────────────────────────────────────────────
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN (
            'octopus_region'
        )
    """)

    # ── Add new optimizer settings ────────────────────────────────────────────
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('force_discharge_threshold_kw', '0.5', 'float', 'optimization',
         'Min discharge kW to trigger Force Discharge mode (defaults to force_charge_threshold_kw)'),
        ('force_discharge_export_min_kw', '0.05', 'float', 'optimization',
         'Min grid export kW guard for Force Discharge mode')
    """)


def downgrade() -> None:
    # Re-add the dropped columns (nullable so existing rows are unaffected)
    with op.batch_alter_table("system_states") as batch_op:
        batch_op.add_column(sa.Column("immersion_main_on", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("immersion_lucy_on", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("battery_discharge_current", sa.Integer(), nullable=True))

    # Re-add the removed setting
    op.execute("""
        INSERT IGNORE INTO system_settings (`key`, `value`, value_type, category, description) VALUES
        ('octopus_region', 'E', 'string', 'octopus', 'Octopus region code')
    """)

    # Remove the new settings
    op.execute("""
        DELETE FROM system_settings
        WHERE `key` IN ('force_discharge_threshold_kw', 'force_discharge_export_min_kw')
    """)
