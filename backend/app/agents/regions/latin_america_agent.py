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


class LatinAmericaGeoAgent(GeoAgent):
    """Latin America geo-agent for Panama Canal and Pacific/Atlantic coast ports."""

    REGION_ID = "latin_america"
    REGION_NAME = "Latin America"
    BBOX = (-85.0, -60.0, -30.0, 15.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
        panama_canal_weight: float = 2.0,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )
        self.panama_canal_weight = panama_canal_weight

    def get_system_prompt(self) -> str:
        """Return Latin America operational context for risk reasoning."""
        return (
            "You are Geo-Agent #07 for Latin America covering both Atlantic and Pacific coasts. "
            "Prioritize risk around Panama Canal throughput (critical global chokepoint), "
            "Port of Santos (Brazil), Callao (Peru), and seasonal Pacific coast storm patterns. "
            "Critical context: Panama Canal drought restrictions impacting vessel depth, "
            "Brazilian soy and iron ore export seasonality, Chilean copper logistics corridor, "
            "and Caribbean hurricane exposure for northern ports. "
            "Elevate risk signals when Panama Canal transit delays increase or when "
            "El Nino/La Nina patterns indicate extended canal draft restrictions."
        )

    async def reason(
        self, events: list[Event], perception_result: PerceptionResult | None = None
    ) -> Decision:
        """Attach Panama Canal weight and seasonality metadata to the assessment."""
        decision = await super().reason(events, perception_result)
        decision["panama_canal_weight"] = self.panama_canal_weight
        decision["draft_restriction_sensitivity"] = "active"
        return decision
