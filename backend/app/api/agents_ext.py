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

"""Extended agent endpoints for stats, tiers, and enhanced listing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.agents.agent_manager import agent_manager
from app.agents.agent_registry import AGENT_REGISTRY, TIER_HIERARCHY
from app.api.schemas.projects import Envelope, EnvelopeMeta

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentStatsResponse(BaseModel):
    """Aggregate statistics across all agents."""

    model_config = ConfigDict(extra="allow")

    total_agents: int
    running_agents: int
    stopped_agents: int
    degraded_agents: int
    by_tier: dict[str, int]
    by_status: dict[str, int]
    by_region: list[dict[str, Any]]


class TierInfo(BaseModel):
    """Information about a single tier level."""

    model_config = ConfigDict(extra="allow")

    tier: int
    name: str
    description: str
    agent_count: int
    regions: list[str]


class TierHierarchyResponse(BaseModel):
    """Full tier hierarchy with parent-child relationships."""

    model_config = ConfigDict(extra="allow")

    tiers: list[TierInfo]
    neighbor_map: dict[str, list[str]]
    total_agents: int


class AgentListItem(BaseModel):
    """Single agent entry in the filtered list."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    region_name: str
    tier: int
    running: bool
    status: str
    last_cycle_at: str | None
    last_assessment: dict[str, Any] | None
    neighbors: list[str]


def _get_agent_tier(region_id: str) -> int:
    config = AGENT_REGISTRY.get(region_id, {})
    return config.get("tier", 1)


def _get_agent_status_label(agent_data: dict[str, Any]) -> str:
    """Derive a human-readable status label from agent data."""
    if not agent_data.get("running", False):
        return "stopped"
    degradation = agent_data.get("degradation_status")
    if degradation and degradation.get("is_degraded", False):
        return "degraded"
    return "running"


@router.get("/stats", response_model=Envelope)
async def get_agent_stats() -> Envelope:
    """Return aggregate statistics across all registered agents."""
    all_agents = agent_manager.list_agents()

    running_count = sum(1 for a in all_agents if a.get("running", False))
    stopped_count = len(all_agents) - running_count
    degraded_count = sum(
        1
        for a in all_agents
        if a.get("degradation_status")
        and a["degradation_status"].get("is_degraded", False)
    )

    by_tier: dict[str, int] = {"1": 0, "2": 0, "3": 0}
    by_status: dict[str, int] = {"running": 0, "stopped": 0, "degraded": 0}

    by_region: list[dict[str, Any]] = []
    for agent_data in all_agents:
        region_id = agent_data.get("region_id", "")
        tier = _get_agent_tier(region_id)
        status = _get_agent_status_label(agent_data)

        by_tier[str(tier)] = by_tier.get(str(tier), 0) + 1
        by_status[status] = by_status.get(status, 0) + 1

        by_region.append(
            {
                "region_id": region_id,
                "region_name": agent_data.get("region_name", ""),
                "tier": tier,
                "status": status,
                "running": agent_data.get("running", False),
            }
        )

    stats = AgentStatsResponse(
        total_agents=len(all_agents),
        running_agents=running_count,
        stopped_agents=stopped_count,
        degraded_agents=degraded_count,
        by_tier=by_tier,
        by_status=by_status,
        by_region=by_region,
    )

    return Envelope(data=stats.model_dump(), error=None, meta=None)


@router.get("/tiers", response_model=Envelope)
async def get_agent_tiers() -> Envelope:
    from app.agents.agent_registry import TIER_1_REGIONS, TIER_2_REGIONS, TIER_3_REGIONS

    all_agents = agent_manager.list_agents()
    agent_region_ids = {a.get("region_id", "") for a in all_agents}

    tiers: list[TierInfo] = []
    for tier_num, tier_data in TIER_HIERARCHY.items():
        region_ids = [e["region_id"] for e in tier_data["regions"]]
        active = [r for r in region_ids if r in agent_region_ids]
        tiers.append(
            TierInfo(
                tier=tier_num,
                name=tier_data["name"],
                description=tier_data["description"],
                agent_count=len(active),
                regions=active,
            )
        )

    neighbor_map = {}
    for rid, agent in agent_manager.agents.items():
        neighbors = getattr(agent, "neighbor_region_ids", [])
        if neighbors:
            neighbor_map[rid] = neighbors

    hierarchy = TierHierarchyResponse(
        tiers=tiers,
        neighbor_map=neighbor_map,
        total_agents=len(all_agents),
    )

    return Envelope(data=hierarchy.model_dump(), error=None, meta=None)


@router.get("/list", response_model=Envelope)
async def list_agents_filtered(
    tier: list[int] | None = Query(default=None, description="Filter by tier level"),
    search: str | None = Query(
        default=None, min_length=1, description="Search by region name or ID"
    ),
    status: str | None = Query(
        default=None, description="Filter by status: running, stopped, degraded"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Envelope:
    """List agents with filtering by tier, search, and status, with pagination."""
    all_agents = agent_manager.list_agents()

    filtered: list[dict[str, Any]] = []
    for agent_data in all_agents:
        region_id = agent_data.get("region_id", "")
        region_name = agent_data.get("region_name", "")
        agent_tier = _get_agent_tier(region_id)
        agent_status = _get_agent_status_label(agent_data)

        if tier is not None and agent_tier not in tier:
            continue

        if search is not None:
            search_lower = search.lower()
            if (
                search_lower not in region_id.lower()
                and search_lower not in region_name.lower()
            ):
                continue

        if status is not None and agent_status != status.lower():
            continue

        neighbors = list(getattr(agent_manager.agents.get(region_id, {}), "neighbor_region_ids", []) or [])
        filtered.append(
            AgentListItem(
                region_id=region_id,
                region_name=region_name,
                tier=agent_tier,
                running=agent_data.get("running", False),
                status=agent_status,
                last_cycle_at=agent_data.get("last_cycle_at"),
                last_assessment=agent_data.get("last_assessment"),
                neighbors=neighbors,
            ).model_dump()
        )

    total = len(filtered)
    paginated = filtered[offset : offset + limit]

    return Envelope(
        data=paginated,
        error=None,
        meta=EnvelopeMeta(total=total, limit=limit, offset=offset),
    )
