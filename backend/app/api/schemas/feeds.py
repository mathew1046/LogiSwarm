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
