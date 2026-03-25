"""add routes table

Revision ID: 20260325_0006
Revises: 20260325_0005
Create Date: 2026-03-25 13:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260325_0006"
down_revision: Union[str, Sequence[str], None] = "20260325_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("route_type", sa.String(length=32), nullable=False),
        sa.Column("origin_region", sa.String(length=128), nullable=False),
        sa.Column("destination_region", sa.String(length=128), nullable=False),
        sa.Column(
            "path",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("cost", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column(
            "transit_hours", sa.Float(), nullable=False, server_default=sa.text("0.0")
        ),
        sa.Column(
            "reliability", sa.Float(), nullable=False, server_default=sa.text("0.9")
        ),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "disrupted", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("disruption_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_routes_origin_region", "routes", ["origin_region"], unique=False
    )
    op.create_index(
        "ix_routes_destination_region", "routes", ["destination_region"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_routes_destination_region", table_name="routes")
    op.drop_index("ix_routes_origin_region", table_name="routes")
    op.drop_table("routes")
