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

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.agents.base_agent import GeoAgent, PerceptionResult
from app.agents.llm_core import ClaudeReasoningCore
from app.agents.memory import SeedMemoryResult, ZepEpisodicMemory
from app.agents.regions.africa_agent import AfricaGeoAgent
from app.agents.regions.china_ea_agent import ChinaEastAsiaGeoAgent
from app.agents.regions.europe_agent import EuropeGeoAgent
from app.agents.regions.gulf_suez_agent import GulfSuezGeoAgent
from app.agents.regions.latin_america_agent import LatinAmericaGeoAgent
from app.agents.regions.north_america_agent import NorthAmericaGeoAgent
from app.agents.regions.se_asia_agent import SEAsiaGeoAgent
from app.agents.regions.south_asia_agent import SouthAsiaGeoAgent
from app.feeds.aggregator import FeedAggregator

try:
    from app.api_rate_limiter import rate_limit

    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False

    def rate_limit(limit: str = "1000/minute"):
        def decorator(func):
            return func

        return decorator


logger = logging.getLogger(__name__)


NEIGHBOR_MAP: dict[str, list[str]] = {
    "se_asia": ["gulf_suez", "china_ea", "south_asia"],
    "europe": ["gulf_suez", "north_america"],
    "gulf_suez": ["se_asia", "europe", "south_asia"],
    "north_america": ["europe", "latin_america"],
    "china_ea": ["se_asia", "south_asia"],
    "south_asia": ["se_asia", "gulf_suez", "china_ea", "africa"],
    "latin_america": ["north_america", "africa"],
    "africa": ["south_asia", "latin_america", "europe"],
}


class Envelope(BaseModel):
    """Standard API envelope for agent manager responses."""

    model_config = ConfigDict(extra="allow")

    data: Any
    error: str | None = None
    meta: dict[str, Any] | None = None


class AgentConfigResponse(BaseModel):
    """Agent configuration parameters."""

    region_id: str
    region_name: str
    poll_interval_seconds: int
    confidence_threshold: float
    auto_act_enabled: bool
    broadcast_to_neighbors: bool
    neighbors: list[str]


class AgentConfigUpdate(BaseModel):
    """Request body for updating agent configuration."""

    poll_interval_seconds: int | None = Field(default=None, ge=30, le=3600)
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_act_enabled: bool | None = None
    broadcast_to_neighbors: bool | None = None


class AgentConfigEnvelope(BaseModel):
    """API envelope for agent config responses."""

    model_config = ConfigDict(extra="allow")

    data: AgentConfigResponse
    error: str | None = None
    meta: dict[str, Any] | None = None


_agent_configs: dict[str, dict[str, Any]] = {}


class AgentManager:
    """Registry and lifecycle manager for all configured geo-agents."""

    def __init__(
        self, llm_client: object | None = None, zep_client: object | None = None
    ) -> None:
        self.llm_client = llm_client or ClaudeReasoningCore()
        self.zep_client = zep_client or ZepEpisodicMemory()
        self.agents: dict[str, GeoAgent] = {}

    async def start_all(self) -> None:
        """Instantiate and start all core Tier-1 geo-agents."""
        if not self.agents:
            self._instantiate_agents()

        for region_id, neighbors in NEIGHBOR_MAP.items():
            self.agents[region_id].set_neighbors(neighbors)

        for agent in self.agents.values():
            await agent.start()

    async def stop_all(self) -> None:
        """Stop every registered geo-agent."""
        for agent in self.agents.values():
            await agent.stop()

    def list_agents(self) -> list[dict[str, Any]]:
        """Return concise runtime status for all agents."""
        return [self._status_payload(agent) for agent in self.agents.values()]

    def get_agent(self, region_id: str) -> GeoAgent:
        """Resolve an agent by region id or raise a 404-style error."""
        agent = self.agents.get(region_id)
        if agent is None:
            raise KeyError(region_id)
        return agent

    def get_agent_status(self, region_id: str) -> dict[str, Any]:
        """Return detailed status for one regional agent."""
        return self._status_payload(self.get_agent(region_id))

    def get_agent_config(self, region_id: str) -> AgentConfigResponse:
        """Return current configuration for one regional agent."""
        agent = self.get_agent(region_id)
        stored_config = _agent_configs.get(region_id, {})
        neighbors = [n for n in NEIGHBOR_MAP.get(region_id, [])]

        return AgentConfigResponse(
            region_id=agent.region_id,
            region_name=agent.region_name,
            poll_interval_seconds=stored_config.get(
                "poll_interval_seconds", agent.poll_interval_seconds
            ),
            confidence_threshold=stored_config.get("confidence_threshold", 0.75),
            auto_act_enabled=stored_config.get("auto_act_enabled", True),
            broadcast_to_neighbors=stored_config.get("broadcast_to_neighbors", True),
            neighbors=neighbors,
        )

    def update_agent_config(
        self, region_id: str, updates: AgentConfigUpdate
    ) -> AgentConfigResponse:
        """Update configuration for one regional agent and hot-reload."""
        agent = self.get_agent(region_id)

        if region_id not in _agent_configs:
            _agent_configs[region_id] = {
                "poll_interval_seconds": agent.poll_interval_seconds,
                "confidence_threshold": 0.75,
                "auto_act_enabled": True,
                "broadcast_to_neighbors": True,
            }

        config = _agent_configs[region_id]

        if updates.poll_interval_seconds is not None:
            config["poll_interval_seconds"] = updates.poll_interval_seconds
            agent.poll_interval_seconds = updates.poll_interval_seconds

        if updates.confidence_threshold is not None:
            config["confidence_threshold"] = updates.confidence_threshold

        if updates.auto_act_enabled is not None:
            config["auto_act_enabled"] = updates.auto_act_enabled

        if updates.broadcast_to_neighbors is not None:
            config["broadcast_to_neighbors"] = updates.broadcast_to_neighbors
            if updates.broadcast_to_neighbors:
                neighbors = NEIGHBOR_MAP.get(region_id, [])
                agent.set_neighbors(neighbors)
            else:
                agent.set_neighbors([])

        return self.get_agent_config(region_id)

    async def force_assess(self, region_id: str) -> dict[str, Any]:
        """Trigger an immediate perceive→reason→act cycle for one agent."""
        agent = self.get_agent(region_id)
        decision = await agent.run_cycle()
        return {
            "region_id": region_id,
            "forced_at": datetime.now(UTC).isoformat(),
            "decision": decision,
        }

    def _instantiate_agents(self) -> None:
        self.agents = {
            SEAsiaGeoAgent.REGION_ID: SEAsiaGeoAgent(
                llm_client=self.llm_client, zep_client=self.zep_client
            ),
            EuropeGeoAgent.REGION_ID: EuropeGeoAgent(
                llm_client=self.llm_client, zep_client=self.zep_client
            ),
            GulfSuezGeoAgent.REGION_ID: GulfSuezGeoAgent(
                llm_client=self.llm_client, zep_client=self.zep_client
            ),
            NorthAmericaGeoAgent.REGION_ID: NorthAmericaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
            ChinaEastAsiaGeoAgent.REGION_ID: ChinaEastAsiaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
            SouthAsiaGeoAgent.REGION_ID: SouthAsiaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
            LatinAmericaGeoAgent.REGION_ID: LatinAmericaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
            AfricaGeoAgent.REGION_ID: AfricaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
        }

    @staticmethod
    def _status_payload(agent: GeoAgent) -> dict[str, Any]:
        degradation_status = agent.last_degradation_status
        return {
            "region_id": agent.region_id,
            "region_name": agent.region_name,
            "running": bool(agent._task and not agent._task.done()),
            "last_cycle_at": agent.last_cycle_at.isoformat()
            if agent.last_cycle_at
            else None,
            "last_assessment": agent.last_decision,
            "degradation_status": {
                "mode": degradation_status.mode if degradation_status else "NORMAL",
                "is_degraded": degradation_status is not None
                and degradation_status.mode != "NORMAL",
                "degraded_connectors": degradation_status.degraded_connectors
                if degradation_status
                else [],
                "cached_data_age_minutes": degradation_status.cached_data_age_minutes
                if degradation_status
                else None,
                "uncertainty_factor": degradation_status.uncertainty_factor
                if degradation_status
                else 0.0,
            }
            if degradation_status
            else None,
        }

    def get_agent_degradation_status(self, region_id: str) -> AgentDegradationResponse:
        """Return the degradation status for one regional agent."""
        agent = self.get_agent(region_id)
        status = agent.last_degradation_status

        if status is None:
            return AgentDegradationResponse(
                region_id=agent.region_id,
                region_name=agent.region_name,
                mode="NORMAL",
                is_degraded=False,
                degraded_connectors=[],
                cached_data_age_minutes=None,
                uncertainty_factor=0.0,
                last_successful_fetch=None,
            )

        return AgentDegradationResponse(
            region_id=agent.region_id,
            region_name=agent.region_name,
            mode=status.mode,
            is_degraded=status.mode != "NORMAL",
            degraded_connectors=status.degraded_connectors,
            cached_data_age_minutes=status.cached_data_age_minutes,
            uncertainty_factor=status.uncertainty_factor,
            last_successful_fetch=status.last_successful_fetch,
        )

    async def get_all_degradation_statuses(self) -> list[AgentDegradationResponse]:
        """Return degradation status for all agents."""
        statuses = []
        for agent in self.agents.values():
            status = agent.last_degradation_status
            if status is None:
                statuses.append(
                    AgentDegradationResponse(
                        region_id=agent.region_id,
                        region_name=agent.region_name,
                        mode="NORMAL",
                        is_degraded=False,
                        degraded_connectors=[],
                        cached_data_age_minutes=None,
                        uncertainty_factor=0.0,
                        last_successful_fetch=None,
                    )
                )
            else:
                statuses.append(
                    AgentDegradationResponse(
                        region_id=agent.region_id,
                        region_name=agent.region_name,
                        mode=status.mode,
                        is_degraded=status.mode != "NORMAL",
                        degraded_connectors=status.degraded_connectors,
                        cached_data_age_minutes=status.cached_data_age_minutes,
                        uncertainty_factor=status.uncertainty_factor,
                        last_successful_fetch=status.last_successful_fetch,
                    )
                )
        return statuses


agent_manager = AgentManager()
router = APIRouter(prefix="/agents", tags=["agents"])


class SeedMemoryRequest(BaseModel):
    """Request body for seeding agent memory from uploaded data."""

    data: str = Field(min_length=1, description="CSV or JSON data string")
    format: str = Field(default="json", description="Data format: 'csv' or 'json'")


class SeedMemoryResponse(BaseModel):
    """Response for agent memory seeding operation."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    episodes_seeded: int
    episodes_skipped: int
    episodes_total: int
    errors: list[str] = Field(default_factory=list)


class AgentDegradationResponse(BaseModel):
    """Response for agent degradation status."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    region_name: str
    mode: str
    is_degraded: bool
    degraded_connectors: list[str]
    cached_data_age_minutes: float | None
    uncertainty_factor: float
    last_successful_fetch: datetime | None


class InterviewRequest(BaseModel):
    """Request body for agent interview."""

    question: str = Field(
        min_length=5, max_length=2000, description="Question to ask the agent"
    )


class InterviewSource(BaseModel):
    """A source cited in an interview response."""

    model_config = ConfigDict(extra="allow")

    episode_id: str | None = None
    content: str | None = None
    severity: str | None = None
    created_at: str | None = None


class InterviewResponse(BaseModel):
    """Response from agent interview."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    region_name: str
    question: str
    answer: str
    sources: list[InterviewSource] = Field(default_factory=list)
    current_risk_level: str
    current_confidence: float
    answered_at: str


@router.get("", response_model=Envelope)
async def list_agents() -> Envelope:
    return Envelope(
        data=agent_manager.list_agents(),
        error=None,
        meta={"total": len(agent_manager.agents)},
    )


@router.get("/{region_id}/status", response_model=Envelope)
async def get_agent_status(region_id: str) -> Envelope:
    try:
        payload = agent_manager.get_agent_status(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None
    return Envelope(data=payload, error=None, meta=None)


@router.get("/{region_id}/config", response_model=AgentConfigEnvelope)
async def get_agent_config(region_id: str) -> AgentConfigEnvelope:
    """Get current agent configuration thresholds, poll intervals, and settings."""
    try:
        config = agent_manager.get_agent_config(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None
    return AgentConfigEnvelope(data=config, error=None, meta=None)


@router.put("/{region_id}/config", response_model=AgentConfigEnvelope)
async def update_agent_config(
    region_id: str, payload: AgentConfigUpdate
) -> AgentConfigEnvelope:
    """Update agent configuration and hot-reload agent on next cycle."""
    try:
        config = agent_manager.update_agent_config(region_id, payload)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None
    return AgentConfigEnvelope(data=config, error=None, meta={"updated": True})


@router.post("/{region_id}/force-assess", response_model=Envelope)
async def force_assess(region_id: str) -> Envelope:
    try:
        payload = await agent_manager.force_assess(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None
    return Envelope(data=payload, error=None, meta=None)


@router.post("/{region_id}/seed-memory", response_model=SeedMemoryResponse)
async def seed_agent_memory(
    region_id: str, payload: SeedMemoryRequest
) -> SeedMemoryResponse:
    """Seed agent episodic memory from CSV or JSON data upload."""
    try:
        agent_manager.get_agent(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None

    data_format = payload.format.lower().strip()
    if data_format not in {"csv", "json"}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{payload.format}'. Must be 'csv' or 'json'.",
        )

    zep_client = ZepEpisodicMemory()
    result = await zep_client.seed_memory_from_data(
        region_id=region_id,
        data=payload.data,
        data_format=data_format,
    )

    logger.info(
        f"Seeded {result.episodes_seeded} episodes into agent memory for region {region_id} "
        f"(skipped {result.episodes_skipped} duplicates)"
    )

    return SeedMemoryResponse(
        region_id=result.region_id,
        episodes_seeded=result.episodes_seeded,
        episodes_skipped=result.episodes_skipped,
        episodes_total=result.episodes_total,
        errors=result.errors,
    )


@router.get("/degradation-status", response_model=Envelope)
async def get_all_degradation_statuses() -> Envelope:
    """Return degradation status for all agents."""
    statuses = await agent_manager.get_all_degradation_statuses()
    return Envelope(
        data=[s.model_dump() for s in statuses],
        error=None,
        meta={"total": len(statuses)},
    )


@router.get("/{region_id}/degradation-status", response_model=Envelope)
async def get_agent_degradation_status(region_id: str) -> Envelope:
    """Return degradation status for one agent."""
    try:
        status = agent_manager.get_agent_degradation_status(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None
    return Envelope(data=status.model_dump(), error=None, meta=None)


@router.post("/{region_id}/interview", response_model=InterviewResponse)
@rate_limit("10/minute")
async def interview_agent(
    region_id: str, payload: InterviewRequest
) -> InterviewResponse:
    """Interview a geo-agent about its region using memory and current state."""
    try:
        agent = agent_manager.get_agent(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None

    result = await agent.interview(payload.question)
    return InterviewResponse(
        region_id=result["region_id"],
        region_name=result["region_name"],
        question=result["question"],
        answer=result["answer"],
        sources=[InterviewSource.model_validate(s) for s in result["sources"]],
        current_risk_level=result["current_risk_level"],
        current_confidence=result["current_confidence"],
        answered_at=result["answered_at"],
    )
