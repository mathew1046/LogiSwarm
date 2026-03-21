"""initial schema with core entities

Revision ID: 20260321_0001
Revises:
Create Date: 2026-03-21 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "geo_regions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("bbox", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "shipment_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shipment_ref", sa.String(length=128), nullable=False),
        sa.Column("carrier", sa.String(length=128), nullable=True),
        sa.Column("origin", sa.String(length=128), nullable=True),
        sa.Column("destination", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("eta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shipment_ref"),
    )

    op.create_table(
        "disruption_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("signal_type", sa.String(length=128), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cascade_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["region_id"], ["geo_regions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_disruption_events_region_id", "disruption_events", ["region_id"], unique=False)
    op.create_index("ix_disruption_events_detected_at", "disruption_events", ["detected_at"], unique=False)

    op.create_table(
        "route_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("disruption_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["disruption_event_id"], ["disruption_events.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_route_recommendations_disruption_event_id",
        "route_recommendations",
        ["disruption_event_id"],
        unique=False,
    )

    op.create_table(
        "agent_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("episode_summary", sa.Text(), nullable=False),
        sa.Column("embedding_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["geo_regions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_episodes_region_id", "agent_episodes", ["region_id"], unique=False)

    op.execute(
        "SELECT create_hypertable('disruption_events', 'detected_at', if_not_exists => TRUE);"
    )


def downgrade() -> None:
    op.drop_index("ix_agent_episodes_region_id", table_name="agent_episodes")
    op.drop_table("agent_episodes")

    op.drop_index("ix_route_recommendations_disruption_event_id", table_name="route_recommendations")
    op.drop_table("route_recommendations")

    op.drop_index("ix_disruption_events_detected_at", table_name="disruption_events")
    op.drop_index("ix_disruption_events_region_id", table_name="disruption_events")
    op.drop_table("disruption_events")

    op.drop_table("shipment_records")
    op.drop_table("geo_regions")
