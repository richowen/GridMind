"""002 — Immersion devices table with seed data for main and lucy tanks.

Revision ID: 002
Revises: 001
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "immersion_devices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("switch_entity_id", sa.String(150), nullable=False),
        sa.Column("temp_sensor_entity_id", sa.String(150)),
        # server_default ensures MariaDB sets 1/0 even when the column is omitted from INSERT
        sa.Column("is_enabled", sa.Boolean, default=True, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer, default=0, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Seed the two known immersion devices (is_enabled defaults to 1 via server_default)
    op.execute("""
        INSERT INTO immersion_devices (name, display_name, switch_entity_id, temp_sensor_entity_id, is_enabled, sort_order)
        VALUES
        ('main', 'Main Hot Water Tank', 'switch.immersion_switch', 'sensor.sonoff_1001e116e1_temperature', 1, 1),
        ('lucy', 'Lucy''s Tank', 'switch.immersion_lucy_switch', 'sensor.t_h_sensor_with_external_probe_temperature_2', 1, 2)
    """)


def downgrade() -> None:
    op.drop_table("immersion_devices")
