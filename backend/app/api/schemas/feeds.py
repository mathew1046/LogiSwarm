from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FeedHealthResponse(BaseModel):
    connector: str
    status: str
    last_successful_fetch: datetime | None
    last_latency_ms: float | None
    event_count_last_hour: int
    poll_interval_seconds: int


class DegradationStatusResponse(BaseModel):
    """Response model for region degradation status."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    mode: str = Field(description="NORMAL, DEGRADED, or OFFLINE")
    all_connectors_failed: bool
    failed_connector_count: int
    total_connector_count: int
    degraded_connectors: list[str]
    last_successful_fetch: datetime | None
    cached_data_age_minutes: float | None
    uncertainty_factor: float = Field(
        description="0.0-1.0 multiplier for confidence reduction"
    )
