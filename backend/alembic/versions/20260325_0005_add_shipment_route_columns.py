"""add shipment route columns

Revision ID: 20260325_0005
Revises: 20260325_0004
Create Date: 2026-03-25 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260325_0005"
down_revision: Union[str, Sequence[str], None] = "20260325_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shipment_records",
        sa.Column(
            "route",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "shipment_records",
        sa.Column("cargo_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "shipment_records",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shipment_records", "updated_at")
    op.drop_column("shipment_records", "cargo_type")
    op.drop_column("shipment_records", "route")
