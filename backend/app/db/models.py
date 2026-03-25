from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GeoRegion(Base):
    __tablename__ = "geo_regions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    bbox: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Polygon in WKT format, e.g. POLYGON((...)).",
    )
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="LOW")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ShipmentRecord(Base):
    __tablename__ = "shipment_records"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    shipment_ref: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    carrier: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    route: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    cargo_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    eta: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DisruptionEvent(Base):
    __tablename__ = "disruption_events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geo_regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(128), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cascade_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RouteRecommendation(Base):
    __tablename__ = "route_recommendations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    disruption_event_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("disruption_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentEpisode(Base):
    __tablename__ = "agent_episodes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    region_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("geo_regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    episode_summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class VesselPosition(Base):
    __tablename__ = "vessel_positions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    vessel_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class DecisionLog(Base):
    __tablename__ = "decision_log"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    region_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    input_events: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_action: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    human_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outcome: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    route_type: Mapped[str] = mapped_column(String(32), nullable=False)
    origin_region: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    destination_region: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    path: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transit_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reliability: Mapped[float] = mapped_column(Float, nullable=False, default=0.9)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    disrupted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disruption_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    disruption_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("disruption_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="post_disruption"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
