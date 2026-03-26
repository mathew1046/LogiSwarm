"""add language column to reports

Revision ID: 20260326_0010
Revises: 20260326_0009
Create Date: 2026-03-26 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260326_0010"
down_revision: Union[str, Sequence[str], None] = "20260326_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("language", sa.String(length=8), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("reports", "language")
