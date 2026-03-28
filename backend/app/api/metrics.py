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

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/metrics", tags=["monitoring"])

agent_reasoning_latency = Histogram(
    "logiswarm_agent_reasoning_latency_seconds",
    "Time spent on agent reasoning cycles",
    ["region_id"],
    buckets=[1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0],
)

disruptions_detected = Counter(
    "logiswarm_disruptions_detected_total",
    "Total number of disruptions detected",
    ["region_id", "severity"],
)

auto_reroutes = Counter(
    "logiswarm_auto_reroutes_total",
    "Total number of automatic reroutes triggered",
    ["region_id", "mode"],
)

llm_tokens_used = Counter(
    "logiswarm_llm_tokens_used_total",
    "Total LLM tokens consumed",
    ["model", "agent_id"],
)

feed_events_ingested = Counter(
    "logiswarm_feed_events_ingested_total",
    "Total events ingested from external feeds",
    ["feed_type", "region_id"],
)

agent_confidence = Gauge(
    "logiswarm_agent_confidence",
    "Current confidence score of each agent",
    ["region_id"],
)

active_shipments = Gauge(
    "logiswarm_active_shipments",
    "Number of active shipments being tracked",
    ["project_id"],
)


def get_metrics() -> bytes:
    return generate_latest()


@router.get("")
async def metrics_endpoint():
    return Response(
        content=get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8"
    )
