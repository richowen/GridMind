"""003 — Rules engine: immersion_smart_rules and temperature_targets with seed rules.

Revision ID: 003
Revises: 002
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "immersion_smart_rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("immersion_id", sa.Integer, sa.ForeignKey("immersion_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("is_enabled", sa.Boolean, default=True, server_default=sa.true()),
        sa.Column("priority", sa.Integer, default=10, server_default=sa.text("10")),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("logic_operator", sa.String(3), default="AND", server_default=sa.text("'AND'")),
        sa.Column("price_enabled", sa.Boolean, default=False, server_default=sa.false()),
        sa.Column("price_operator", sa.String(5)),
        sa.Column("price_threshold_pence", sa.Float),
        sa.Column("soc_enabled", sa.Boolean, default=False, server_default=sa.false()),
        sa.Column("soc_operator", sa.String(5)),
        sa.Column("soc_threshold_percent", sa.Float),
        sa.Column("solar_enabled", sa.Boolean, default=False, server_default=sa.false()),
        sa.Column("solar_operator", sa.String(5)),
        sa.Column("solar_threshold_kw", sa.Float),
        sa.Column("temp_enabled", sa.Boolean, default=False, server_default=sa.false()),
        sa.Column("temp_operator", sa.String(5)),
        sa.Column("temp_threshold_c", sa.Float),
        sa.Column("time_enabled", sa.Boolean, default=False, server_default=sa.false()),
        sa.Column("time_start", sa.Time),
        sa.Column("time_end", sa.Time),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("idx_device_priority", "immersion_smart_rules", ["immersion_id", "is_enabled", "priority"])

    op.create_table(
        "temperature_targets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("immersion_id", sa.Integer, sa.ForeignKey("immersion_devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_name", sa.String(100), nullable=False),
        sa.Column("target_temp_c", sa.Float, nullable=False),
        sa.Column("target_time", sa.Time, nullable=False),
        sa.Column("days_of_week", sa.String(20), nullable=False),
        sa.Column("heating_rate_c_per_hour", sa.Float, default=5.0, server_default=sa.text("5.0")),
        sa.Column("buffer_minutes", sa.Integer, default=30, server_default=sa.text("30")),
        sa.Column("is_enabled", sa.Boolean, default=True, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Seed default smart rules for both devices
    op.execute("""
        INSERT INTO immersion_smart_rules
            (immersion_id, rule_name, priority, action, logic_operator, price_enabled, price_operator, price_threshold_pence)
        VALUES
            (1, 'Negative Price', 1, 'ON', 'AND', TRUE, '<', 0.0),
            (2, 'Negative Price', 1, 'ON', 'AND', TRUE, '<', 0.0)
    """)
    op.execute("""
        INSERT INTO immersion_smart_rules
            (immersion_id, rule_name, priority, action, logic_operator,
             price_enabled, price_operator, price_threshold_pence,
             soc_enabled, soc_operator, soc_threshold_percent)
        VALUES
            (1, 'Very Cheap + Full Battery', 2, 'ON', 'AND', TRUE, '<', 2.0, TRUE, '>=', 95.0),
            (2, 'Very Cheap + Full Battery', 2, 'ON', 'AND', TRUE, '<', 2.0, TRUE, '>=', 95.0)
    """)
    op.execute("""
        INSERT INTO immersion_smart_rules
            (immersion_id, rule_name, priority, action, logic_operator,
             solar_enabled, solar_operator, solar_threshold_kw,
             soc_enabled, soc_operator, soc_threshold_percent)
        VALUES
            (1, 'Solar Surplus', 3, 'ON', 'AND', TRUE, '>=', 5.0, TRUE, '>=', 90.0),
            (2, 'Solar Surplus', 3, 'ON', 'AND', TRUE, '>=', 5.0, TRUE, '>=', 90.0)
    """)
    op.execute("""
        INSERT INTO immersion_smart_rules
            (immersion_id, rule_name, priority, action, logic_operator, temp_enabled, temp_operator, temp_threshold_c)
        VALUES
            (1, 'Overheat Protection', 99, 'OFF', 'AND', TRUE, '>=', 70.0),
            (2, 'Overheat Protection', 99, 'OFF', 'AND', TRUE, '>=', 70.0)
    """)


def downgrade() -> None:
    op.drop_table("temperature_targets")
    op.drop_table("immersion_smart_rules")
