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

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RouteComparison(BaseModel):
    """Route details for comparison in reroute analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    route_type: str
    origin_region: str
    destination_region: str
    path: dict[str, Any]
    cost: float
    transit_hours: float
    reliability: float
    active: bool
    disrupted: bool


class RerouteAnalysis(BaseModel):
    """Analysis result with LLM-generated reasoning."""

    analysis_id: UUID
    shipment_ref: str
    current_route: RouteComparison
    proposed_route: RouteComparison
    delta_cost: float
    delta_transit_hours: float
    delta_reliability: float
    risk_assessment: str
    reasoning: str
    recommendation: str = Field(pattern="^(accept|reject|review)$")
    confidence: float = Field(ge=0.0, le=1.0)
    cascade_impact: list[str] = Field(default_factory=list)


class RerouteExecuteResponse(BaseModel):
    """Execution result for reroute action."""

    execution_id: UUID
    shipment_ref: str
    previous_route_id: UUID
    new_route_id: UUID
    status: str
    executed_at: datetime


class RerouteRequest(BaseModel):
    """Request body for reroute analysis."""

    shipment_ref: str = Field(min_length=1, max_length=128)
    current_route_id: UUID
    proposed_route_id: UUID
    reason: str = Field(min_length=1, max_length=500)


class RerouteResponse(BaseModel):
    """Response body for reroute analysis."""

    analysis_id: UUID
    shipment_ref: str
    current_route: RouteComparison
    proposed_route: RouteComparison
    delta_cost: float
    delta_transit_hours: float
    delta_reliability: float
    risk_assessment: str
    reasoning: str
    recommendation: str
    confidence: float
    cascade_impact: list[str]


class RerouteExecuteRequest(BaseModel):
    """Request body for reroute execution."""

    analysis_id: UUID
    shipment_ref: str = Field(min_length=1, max_length=128)
    new_route_id: UUID
    approved_by: str = Field(min_length=1, max_length=255)


class RerouteEnvelope(BaseModel):
    """Standard API envelope for reroute endpoints."""

    model_config = ConfigDict(extra="allow")

    data: object
    error: str | None = None
    meta: dict[str, Any] | None = None