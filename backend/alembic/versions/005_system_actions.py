"""005 — System actions audit log table.

Revision ID: 005
Revises: 004
Create Date: 2025-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(150), nullable=False),
        sa.Column("old_value", sa.String(100)),
        sa.Column("new_value", sa.String(100), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("success", sa.Boolean, default=True, server_default=sa.true()),
    )
    op.create_index("idx_action_timestamp", "system_actions", ["timestamp"])
    op.create_index("idx_action_type", "system_actions", ["action_type"])
    op.create_index("idx_action_entity", "system_actions", ["entity_id"])


def downgrade() -> None:
    op.drop_table("system_actions")
