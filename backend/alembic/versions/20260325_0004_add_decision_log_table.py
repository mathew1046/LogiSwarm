"""add decision log table

Revision ID: 20260325_0004
Revises: 20260321_0003
Create Date: 2026-03-25 10:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260325_0004"
down_revision: Union[str, Sequence[str], None] = "20260321_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "decision_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("region_id", sa.String(length=128), nullable=False),
        sa.Column("decision_type", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("input_events", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_action", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("human_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_log_project_id", "decision_log", ["project_id"], unique=False)
    op.create_index("ix_decision_log_region_id", "decision_log", ["region_id"], unique=False)
    op.create_index("ix_decision_log_created_at", "decision_log", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_decision_log_created_at", table_name="decision_log")
    op.drop_index("ix_decision_log_region_id", table_name="decision_log")
    op.drop_index("ix_decision_log_project_id", table_name="decision_log")
    op.drop_table("decision_log")
