"""add predicted_eta and delay_hours to shipment_records

Revision ID: 20260326_0008
Revises: 20260325_0007
Create Date: 2026-03-26 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260326_0008"
down_revision: Union[str, Sequence[str], None] = "20260325_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shipment_records",
        sa.Column("predicted_eta", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "shipment_records",
        sa.Column("delay_hours", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shipment_records", "delay_hours")
    op.drop_column("shipment_records", "predicted_eta")
