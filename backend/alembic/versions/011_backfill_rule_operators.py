"""011 — Backfill NULL operators in immersion_smart_rules to sensible defaults.

Rules saved before operator defaults were enforced may have NULL operator columns,
causing 'Unknown operator: None' warnings and rules never firing.

Revision ID: 011
Revises: 010
Create Date: 2026-04-23
"""
from alembic import op

revision = "011"
down_revision = "010"


def upgrade() -> None:
    op.execute("UPDATE immersion_smart_rules SET price_operator='<'  WHERE price_operator IS NULL")
    op.execute("UPDATE immersion_smart_rules SET soc_operator='>='   WHERE soc_operator IS NULL")
    op.execute("UPDATE immersion_smart_rules SET solar_operator='>=' WHERE solar_operator IS NULL")
    op.execute("UPDATE immersion_smart_rules SET temp_operator='<'   WHERE temp_operator IS NULL")


def downgrade() -> None:
    pass  # NULL operators are invalid — no point restoring them
