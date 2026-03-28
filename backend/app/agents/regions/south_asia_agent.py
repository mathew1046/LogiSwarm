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

from app.agents.base_agent import Decision, Event, GeoAgent, PerceptionResult


class SouthAsiaGeoAgent(GeoAgent):
    """South Asia geo-agent focused on Indian Ocean and Bay of Bengal logistics."""

    REGION_ID = "south_asia"
    REGION_NAME = "South Asia / Indian Ocean"
    BBOX = (68.0, -5.0, 95.0, 25.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
        cyclone_season_weight: float = 1.5,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )
        self.cyclone_season_weight = cyclone_season_weight

    def get_system_prompt(self) -> str:
        """Return South Asia operational context for risk reasoning."""
        return (
            "You are Geo-Agent #06 for South Asia and the Indian Ocean. "
            "Prioritize resilience across Colombo, Chennai, Mumbai, and Bay of Bengal shipping lanes. "
            "Critical context: Indian subcontinent port capacity, monsoon cyclone season (April-December), "
            "Bay of Bengal cyclone belt with frequent severe weather disruptions, Sri Lanka transshipment gateway, "
            "and emerging hinterland logistics constraints from manufacturing inland shifts. "
            "Elevate risk signals during pre-monsoon and post-monsoon transition windows when port "
            "operations face cumulative weather delays."
        )

    async def reason(
        self, events: list[Event], perception_result: PerceptionResult | None = None
    ) -> Decision:
        """Attach region-specific cyclone season sensitivity to the assessment."""
        decision = await super().reason(events, perception_result)
        decision["cyclone_season_weight"] = self.cyclone_season_weight
        decision["monsoon_sensitivity"] = "active"
        return decision
