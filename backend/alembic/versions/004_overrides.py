"""004 — Manual overrides table.

Revision ID: 004
Revises: 003
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manual_overrides",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("immersion_id", sa.Integer, sa.ForeignKey("immersion_devices.id"), nullable=False),
        sa.Column("immersion_name", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("desired_state", sa.Boolean, nullable=False),
        sa.Column("source", sa.String(50), default="user"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("cleared_at", sa.DateTime),
        sa.Column("cleared_by", sa.String(50)),
    )
    op.create_index("idx_active_immersion", "manual_overrides", ["immersion_id", "is_active", "expires_at"])


def downgrade() -> None:
    op.drop_table("manual_overrides")
