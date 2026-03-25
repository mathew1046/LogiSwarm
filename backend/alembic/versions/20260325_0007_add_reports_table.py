"""add reports table

Revision ID: 20260325_0007
Revises: 20260325_0006
Create Date: 2026-03-25 14:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260325_0007"
down_revision: Union[str, Sequence[str], None] = "20260325_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("disruption_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "report_type",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'post_disruption'::text"),
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["disruption_id"], ["disruption_events.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_reports_project_id", "reports", ["project_id"], unique=False)
    op.create_index(
        "ix_reports_disruption_id", "reports", ["disruption_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_reports_disruption_id", table_name="reports")
    op.drop_index("ix_reports_project_id", table_name="reports")
    op.drop_table("reports")
