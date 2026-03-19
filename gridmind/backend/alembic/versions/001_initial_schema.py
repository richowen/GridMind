"""001 — Initial schema: electricity_prices, optimization_results, system_states

Revision ID: 001
Revises:
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "electricity_prices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("valid_from", sa.DateTime, nullable=False),
        sa.Column("valid_to", sa.DateTime, nullable=False),
        sa.Column("price_pence", sa.Float, nullable=False),
        sa.Column("classification", sa.String(20)),
    )
    op.create_index("idx_valid_from", "electricity_prices", ["valid_from"])
    op.create_index("idx_valid_to", "electricity_prices", ["valid_to"])

    op.create_table(
        "optimization_results",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("current_soc", sa.Float),
        sa.Column("current_solar_kw", sa.Float),
        sa.Column("current_price_pence", sa.Float),
        sa.Column("recommended_mode", sa.String(50)),
        sa.Column("recommended_discharge_current", sa.Integer),
        sa.Column("optimization_status", sa.String(20)),
        sa.Column("optimization_time_ms", sa.Float),
        sa.Column("objective_value", sa.Float),
        sa.Column("decision_reason", sa.Text),
        sa.Column("next_action_time", sa.DateTime),
    )
    op.create_index("idx_opt_timestamp", "optimization_results", ["timestamp"])

    op.create_table(
        "system_states",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("battery_soc", sa.Float),
        sa.Column("battery_mode", sa.String(50)),
        sa.Column("battery_discharge_current", sa.Integer),
        sa.Column("solar_power_kw", sa.Float),
        sa.Column("solar_forecast_today_kwh", sa.Float),
        sa.Column("solar_forecast_next_hour_kw", sa.Float),
        sa.Column("current_price_pence", sa.Float),
        sa.Column("immersion_main_on", sa.Boolean),
        sa.Column("immersion_lucy_on", sa.Boolean),
    )
    op.create_index("idx_state_timestamp", "system_states", ["timestamp"])


def downgrade() -> None:
    op.drop_table("system_states")
    op.drop_table("optimization_results")
    op.drop_table("electricity_prices")
