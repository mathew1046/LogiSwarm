from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CascadeRiskRequest(BaseModel):
    trigger_region: str = Field(min_length=1)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class SimulateRequest(BaseModel):
    scenario: str = Field(min_length=1)
    start_date: datetime
    end_date: datetime


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
