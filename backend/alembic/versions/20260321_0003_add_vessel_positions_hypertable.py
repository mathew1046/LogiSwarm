"""add vessel_positions hypertable

Revision ID: 20260321_0003
Revises: 20260321_0002
Create Date: 2026-03-21 00:50:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_0003"
down_revision: Union[str, Sequence[str], None] = "20260321_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vessel_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vessel_id", sa.String(length=128), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "raw",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint(
            "id", "timestamp"
        ),  # Composite key for TimescaleDB hypertable
    )
    op.create_index(
        "ix_vessel_positions_vessel_id", "vessel_positions", ["vessel_id"], unique=False
    )

    op.execute(
        "SELECT create_hypertable('vessel_positions', 'timestamp', if_not_exists => TRUE);"
    )


def downgrade() -> None:
    op.drop_index("ix_vessel_positions_timestamp", table_name="vessel_positions")
    op.drop_index("ix_vessel_positions_vessel_id", table_name="vessel_positions")
    op.drop_table("vessel_positions")
