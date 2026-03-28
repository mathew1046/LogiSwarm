# LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
# Copyright (C) 2025 LogiSwarm Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_manager import NEIGHBOR_MAP, agent_manager
from app.bus.publisher import publish
from app.db.models import DisruptionEvent
from app.db.session import get_db_session
from app.orchestrator.graph_memory import graph_memory_manager

router = APIRouter(prefix="/disruptions", tags=["disruptions"])


class DisruptionEnvelope(BaseModel):
    """Standard API envelope for disruption endpoints."""

    model_config = ConfigDict(extra="allow")

    data: Any
    error: str | None = None
    meta: dict[str, Any] | None = None


class DisruptionResponse(BaseModel):
    """Disruption event response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    region_id: UUID
    severity: str
    signal_type: str
    detected_at: datetime
    resolved_at: datetime | None = None
    cascade_score: float | None = None


class ResolveDisruptionRequest(BaseModel):
    """Request body for resolving a disruption event."""

    resolution_summary: str = Field(min_length=10, max_length=2000)
    propagate_to_neighbors: bool = Field(default=True)


class GraphMemoryUpdateResponse(BaseModel):
    """Response for graph memory update operation."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    disruption_id: str
    nodes_added: int
    edges_added: int
    entities: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    propagated_to: list[str]


@router.get("", response_model=DisruptionEnvelope)
async def list_disruptions(
    severity: str | None = Query(default=None, description="Filter by severity"),
    region_id: str | None = Query(default=None, description="Filter by region ID"),
    resolved: bool | None = Query(
        default=None, description="Filter by resolution status"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> DisruptionEnvelope:
    """List disruption events with optional filtering."""
    stmt = select(DisruptionEvent)

    if severity:
        stmt = stmt.where(DisruptionEvent.severity == severity.upper())
    if region_id:
        try:
            region_uuid = UUID(region_id)
            stmt = stmt.where(DisruptionEvent.region_id == region_uuid)
        except ValueError:
            pass
    if resolved is not None:
        if resolved:
            stmt = stmt.where(DisruptionEvent.resolved_at.is_not(None))
        else:
            stmt = stmt.where(DisruptionEvent.resolved_at.is_(None))

    stmt = stmt.order_by(DisruptionEvent.detected_at.desc()).limit(limit).offset(offset)

    result = await session.execute(stmt)
    disruptions = result.scalars().all()

    return DisruptionEnvelope(
        data=[DisruptionResponse.model_validate(d) for d in disruptions],
        error=None,
        meta={"limit": limit, "offset": offset},
    )


@router.get("/{disruption_id}", response_model=DisruptionEnvelope)
async def get_disruption(
    disruption_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DisruptionEnvelope:
    """Get a specific disruption event by ID."""
    disruption = await session.get(DisruptionEvent, disruption_id)
    if disruption is None:
        raise HTTPException(status_code=404, detail="Disruption not found")

    return DisruptionEnvelope(
        data=DisruptionResponse.model_validate(disruption),
        error=None,
        meta=None,
    )


@router.post("/{disruption_id}/resolve", response_model=DisruptionEnvelope)
async def resolve_disruption(
    disruption_id: UUID,
    payload: ResolveDisruptionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> DisruptionEnvelope:
    """
    Mark a disruption as resolved and trigger graph memory update.

    Extracts entities and relationships from the disruption context,
    updates the graph memory, and propagates to neighboring agents.
    """
    disruption = await session.get(DisruptionEvent, disruption_id)
    if disruption is None:
        raise HTTPException(status_code=404, detail="Disruption not found")

    if disruption.resolved_at is not None:
        raise HTTPException(
            status_code=400,
            detail="Disruption is already resolved",
        )

    disruption.resolved_at = datetime.now(UTC)
    await session.commit()

    region_id_str = str(disruption.region_id)
    neighbor_regions: list[str] = []
    if payload.propagate_to_neighbors:
        neighbor_regions = NEIGHBOR_MAP.get(region_id_str, [])

    graph_update = await graph_memory_manager.update_graph_on_resolution(
        region_id=region_id_str,
        disruption_id=str(disruption_id),
        disruption_text=disruption.signal_type,
        resolution_summary=payload.resolution_summary,
        neighbor_regions=neighbor_regions,
    )

    await publish(
        "disruption.resolved",
        {
            "event_type": "disruption_resolved",
            "disruption_id": str(disruption_id),
            "region_id": region_id_str,
            "resolved_at": disruption.resolved_at.isoformat(),
            "graph_update": {
                "nodes_added": graph_update.nodes_added,
                "edges_added": graph_update.edges_added,
                "propagated_to": graph_update.propagated_to,
            },
        },
    )

    return DisruptionEnvelope(
        data={
            "disruption": DisruptionResponse.model_validate(disruption),
            "graph_update": GraphMemoryUpdateResponse(
                region_id=graph_update.region_id,
                disruption_id=graph_update.disruption_id,
                nodes_added=graph_update.nodes_added,
                edges_added=graph_update.edges_added,
                entities=[e.model_dump() for e in graph_update.entities],
                relationships=[r.model_dump() for r in graph_update.relationships],
                propagated_to=graph_update.propagated_to,
            ).model_dump(),
        },
        error=None,
        meta={"propagated": payload.propagate_to_neighbors},
    )


@router.get("/{disruption_id}/graph-context", response_model=DisruptionEnvelope)
async def get_graph_context(
    disruption_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DisruptionEnvelope:
    """Get graph memory context derived from a resolved disruption."""
    disruption = await session.get(DisruptionEvent, disruption_id)
    if disruption is None:
        raise HTTPException(status_code=404, detail="Disruption not found")

    if disruption.resolved_at is None:
        raise HTTPException(
            status_code=400,
            detail="Disruption is not yet resolved",
        )

    region_id_str = str(disruption.region_id)
    updates = graph_memory_manager.get_region_graph_updates(region_id_str)

    matching_updates = [
        u for u in updates if str(u.disruption_id) == str(disruption_id)
    ]

    if not matching_updates:
        return DisruptionEnvelope(
            data={"entities": [], "relationships": []},
            error=None,
            meta={"disruption_id": str(disruption_id)},
        )

    latest_update = matching_updates[-1]
    return DisruptionEnvelope(
        data={
            "entities": [e.model_dump() for e in latest_update.entities],
            "relationships": [r.model_dump() for r in latest_update.relationships],
        },
        error=None,
        meta={
            "disruption_id": str(disruption_id),
            "updated_at": latest_update.updated_at.isoformat(),
        },
    )
