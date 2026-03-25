from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.agents.base_agent import GeoAgent
from app.agents.llm_core import ClaudeReasoningCore
from app.agents.memory import ZepEpisodicMemory
from app.agents.regions.china_ea_agent import ChinaEastAsiaGeoAgent
from app.agents.regions.europe_agent import EuropeGeoAgent
from app.agents.regions.gulf_suez_agent import GulfSuezGeoAgent
from app.agents.regions.north_america_agent import NorthAmericaGeoAgent
from app.agents.regions.se_asia_agent import SEAsiaGeoAgent


class Envelope(BaseModel):
    """Standard API envelope for agent manager responses."""

    model_config = ConfigDict(extra="allow")

    data: Any
    error: str | None = None
    meta: dict[str, Any] | None = None


class AgentManager:
    """Registry and lifecycle manager for all configured geo-agents."""

    def __init__(self, llm_client: object | None = None, zep_client: object | None = None) -> None:
        self.llm_client = llm_client or ClaudeReasoningCore()
        self.zep_client = zep_client or ZepEpisodicMemory()
        self.agents: dict[str, GeoAgent] = {}

    async def start_all(self) -> None:
        """Instantiate and start all core Tier-1 geo-agents."""
        if not self.agents:
            self._instantiate_agents()

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
            SEAsiaGeoAgent.REGION_ID: SEAsiaGeoAgent(llm_client=self.llm_client, zep_client=self.zep_client),
            EuropeGeoAgent.REGION_ID: EuropeGeoAgent(llm_client=self.llm_client, zep_client=self.zep_client),
            GulfSuezGeoAgent.REGION_ID: GulfSuezGeoAgent(llm_client=self.llm_client, zep_client=self.zep_client),
            NorthAmericaGeoAgent.REGION_ID: NorthAmericaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
            ChinaEastAsiaGeoAgent.REGION_ID: ChinaEastAsiaGeoAgent(
                llm_client=self.llm_client,
                zep_client=self.zep_client,
            ),
        }

    @staticmethod
    def _status_payload(agent: GeoAgent) -> dict[str, Any]:
        return {
            "region_id": agent.region_id,
            "region_name": agent.region_name,
            "running": bool(agent._task and not agent._task.done()),
            "last_cycle_at": agent.last_cycle_at.isoformat() if agent.last_cycle_at else None,
            "last_assessment": agent.last_decision,
        }


agent_manager = AgentManager()
router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=Envelope)
async def list_agents() -> Envelope:
    return Envelope(data=agent_manager.list_agents(), error=None, meta={"total": len(agent_manager.agents)})


@router.get("/{region_id}/status", response_model=Envelope)
async def get_agent_status(region_id: str) -> Envelope:
    try:
        payload = agent_manager.get_agent_status(region_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent '{region_id}' not found") from None
    return Envelope(data=payload, error=None, meta=None)


@router.post("/{region_id}/force-assess", response_model=Envelope)
async def force_assess(region_id: str) -> Envelope:
    try:
        payload = await agent_manager.force_assess(region_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent '{region_id}' not found") from None
    return Envelope(data=payload, error=None, meta=None)
