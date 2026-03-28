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

from fastapi import APIRouter, Query

from app.api.schemas.feeds import DegradationStatusResponse, FeedHealthResponse
from app.api.schemas.projects import Envelope, EnvelopeMeta
from app.feeds.aggregator import FeedAggregator

router = APIRouter(prefix="/feeds", tags=["feeds"])
aggregator = FeedAggregator()


@router.get("/health", response_model=Envelope)
async def get_feed_health(
    region_id: str = Query(default="se_asia", min_length=1),
) -> Envelope:
    """Return feed connector health with degradation detection and event counts."""
    health = await aggregator.get_connectors_health(
        region_id=region_id, lookback_minutes=60
    )

    return Envelope(
        data=[FeedHealthResponse.model_validate(item) for item in health],
        error=None,
        meta=EnvelopeMeta(total=len(health), limit=len(health), offset=0),
    )


@router.get("/degradation-status", response_model=Envelope)
async def get_degradation_status(
    region_id: str = Query(default="se_asia", min_length=1),
) -> Envelope:
    """Return the current degradation status for a region's feed system.

    Indicates whether the system is operating in NORMAL, DEGRADED, or OFFLINE mode.
    In DEGRADED/OFFLINE mode, cached data is used with increased uncertainty.
    """
    status = await aggregator.get_degradation_status(region_id)

    return Envelope(
        data=DegradationStatusResponse.model_validate(status),
        error=None,
        meta={"mode": status.mode, "uncertainty_factor": status.uncertainty_factor},
    )
