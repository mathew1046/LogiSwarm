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
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CascadeRiskRequest(BaseModel):
    trigger_region: str = Field(min_length=1)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class SimulateRequest(BaseModel):
    scenario: str = Field(min_length=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    scenario_id: str | None = None


class RouteOptimizeRequest(BaseModel):
    origin: str
    destination: str
    current_route: list[str] = Field(default_factory=list)
    disrupted_regions: list[str] = Field(default_factory=list)


class EscalationRequest(BaseModel):
    project_id: str
    region_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    input_events: dict[str, object] = Field(default_factory=dict)
    output_action: dict[str, object] = Field(default_factory=dict)
    human_override: bool = False


class OrchestratorEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: object
    error: str | None = None
    meta: dict | None = None
