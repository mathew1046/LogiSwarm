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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DisruptionEvent
from app.db.session import get_db_session
from app.orchestrator.inventory_advisor import InventoryAdvisor, inventory_advisor

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class InventoryRecommendationEnvelope(BaseModel):
    """Standard API envelope for inventory recommendation responses."""

    model_config = ConfigDict(extra="allow")

    data: Any
    error: str | None = None
    meta: dict[str, Any] | None = None


class InventoryRecommendationResponse(BaseModel):
    """Response schema for inventory buffer recommendations."""

    model_config = ConfigDict(from_attributes=True)

    disruption_id: str
    trigger_region: str
    severity: str
    estimated_duration_days: float
    affected_destinations: list[dict[str, Any]]
    generated_at: datetime


@router.get("/inventory", response_model=InventoryRecommendationEnvelope)
async def get_inventory_recommendations(
    disruption_id: str | None = Query(default=None, description="Disruption event ID"),
    trigger_region: str | None = Query(default=None, description="Trigger region ID"),
    severity: str | None = Query(
        default=None, description="Disruption severity (LOW/MEDIUM/HIGH/CRITICAL)"
    ),
    estimated_duration_days: float | None = Query(
        default=None,
        ge=0.1,
        le=365,
        description="Estimated disruption duration in days",
    ),
    product_categories: str | None = Query(
        default=None, description="Comma-separated product categories"
    ),
    destination_regions: str | None = Query(
        default=None, description="Comma-separated destination regions"
    ),
    session: AsyncSession = Depends(get_db_session),
) -> InventoryRecommendationEnvelope:
    """
    Get inventory buffer recommendations for a disruption event.

    If disruption_id is provided, uses the stored disruption event.
    Otherwise, uses trigger_region, severity, and estimated_duration_days parameters.
    """
    trigger = trigger_region
    sev = (severity or "MEDIUM").upper()
    duration = estimated_duration_days or 7.0
    categories = None
    destinations = None

    if disruption_id:
        try:
            event_uuid = UUID(disruption_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid disruption_id format. Must be a valid UUID.",
            ) from None

        stmt = select(DisruptionEvent).where(DisruptionEvent.id == event_uuid)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()

        if event is None:
            raise HTTPException(
                status_code=404,
                detail=f"Disruption event '{disruption_id}' not found.",
            )

        trigger = str(event.region_id)
        sev = (event.severity or "MEDIUM").upper()
        duration = 7.0

        if event.cascade_score:
            duration = min(event.cascade_score * 10, 30.0)

    elif not trigger:
        raise HTTPException(
            status_code=400,
            detail="Either 'disruption_id' or 'trigger_region' must be provided.",
        )

    if product_categories:
        categories = [
            cat.strip() for cat in product_categories.split(",") if cat.strip()
        ]

    if destination_regions:
        destinations = [
            dest.strip() for dest in destination_regions.split(",") if dest.strip()
        ]

    allowed_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    if sev not in allowed_severities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity '{severity}'. Must be one of: {', '.join(allowed_severities)}",
        )

    recommendation = inventory_advisor.recommend(
        disruption_id=disruption_id
        or f"adhoc-{trigger}-{datetime.now(UTC).isoformat()}",
        trigger_region=trigger,
        severity=sev,
        estimated_duration_days=duration,
        affected_product_categories=categories,
        destination_regions=destinations,
    )

    return InventoryRecommendationEnvelope(
        data=recommendation.model_dump(mode="json"),
        error=None,
        meta={
            "trigger_region": trigger,
            "severity": sev,
            "duration_days": duration,
        },
    )
