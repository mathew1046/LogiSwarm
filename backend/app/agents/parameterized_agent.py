from __future__ import annotations

from typing import Any

from app.agents.base_agent import GeoAgent, PerceptionResult
from app.agents.llm_core import ClaudeReasoningCore
from app.agents.memory import ZepEpisodicMemory
from app.feeds.aggregator import FeedAggregator


class ParameterizedGeoAgent(GeoAgent):
    def __init__(
        self,
        config: dict[str, Any],
        llm_client: Any | None = None,
        zep_client: Any | None = None,
        aggregator: FeedAggregator | None = None,
    ) -> None:
        self.config = config
        self.tier = config.get("tier", 3)
        self.specialization = config.get("specialization", "seaport")
        self.key_locations = config.get("key_locations", [])
        self.prompt_weights = config.get("prompt_weights", {})
        self.seasonal_risks = config.get("seasonal_risks", [])
        self.trade_lanes = config.get("trade_lanes", [])
        self.parent_region = config.get("parent_region")

        bbox = config.get("bbox", (0.0, 0.0, 1.0, 1.0))

        super().__init__(
            region_id=config["region_id"],
            region_name=config["region_name"],
            bbox=bbox,
            llm_client=llm_client or ClaudeReasoningCore(),
            zep_client=zep_client or ZepEpisodicMemory(),
            poll_interval_seconds=config.get("poll_interval_seconds", 180),
            aggregator=aggregator,
        )

    def get_system_prompt(self) -> str:
        spec_desc = {
            "seaport": "major seaport logistics node",
            "seaport_cluster": "cluster of major seaports",
            "airport": "international air cargo hub",
            "air_hub": "air cargo hub serving express and freight",
            "chokepoint": "critical maritime chokepoint",
            "rail_hub": "intermodal rail corridor hub",
            "dry_port": "inland dry port and container depot",
            "regional": "regional logistics monitoring zone",
            "terminal": "terminal and logistics facility",
            "logistics_hub": "multi-modal logistics hub",
        }.get(self.specialization, "logistics monitoring node")

        tier_desc = {
            1: "Tier 1 - Regional monitoring zone covering a major trade corridor",
            2: "Tier 2 - Focused monitoring of a {}",
            3: "Tier 3 - Individual monitoring of a {}",
        }.get(self.tier, "Tier 3 - Individual monitoring node")

        locations_str = ", ".join(self.key_locations[:5]) if self.key_locations else "this area"
        risks_str = "; ".join(self.seasonal_risks) if self.seasonal_risks else "none currently flagged"
        lanes_str = "; ".join(self.trade_lanes[:3]) if self.trade_lanes else "local routes"

        tier_fill = f" {spec_desc}" if self.tier > 1 else ""

        prompt = (
            f"You are the {self.region_name} Geo-Agent (ID: {self.region_id}). "
            f"{tier_desc.format(spec_desc) if '{}' in tier_desc else tier_desc}.\n\n"
            f"Coverage: {locations_str}.\n"
            f"Key shipping lanes: {lanes_str}.\n"
            f"Seasonal risks: {risks_str}.\n\n"
            f"Your specialization: {spec_desc}. "
            f"Monitor vessel movements, port conditions, weather events, and geopolitical signals "
            f"relevant to {locations_str}. "
            f"Assess disruptions, estimate confidence, and recommend actions.\n\n"
            f"Respond with structured JSON: severity (LOW/MEDIUM/HIGH/CRITICAL), "
            f"confidence (0.0-1.0), affected_routes, recommended_actions, and reasoning."
        )
        return prompt

    def status_payload(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "tier": self.tier,
            "specialization": self.specialization,
            "parent_region": self.parent_region,
            "running": bool(self._task and not self._task.done()),
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "poll_interval_seconds": self.poll_interval_seconds,
            "confidence_threshold": self.config.get("confidence_threshold", 0.75),
            "last_assessment": self.last_decision,
            "key_locations": self.key_locations,
            "degradation_status": {
                "mode": self.last_degradation_status.mode if self.last_degradation_status else "NORMAL",
                "is_degraded": self.last_degradation_status is not None and self.last_degradation_status.mode != "NORMAL",
                "degraded_connectors": self.last_degradation_status.degraded_connectors if self.last_degradation_status else [],
                "cached_data_age_minutes": self.last_degradation_status.cached_data_age_minutes if self.last_degradation_status else None,
                "uncertainty_factor": self.last_degradation_status.uncertainty_factor if self.last_degradation_status else 0.0,
            } if self.last_degradation_status else None,
        }