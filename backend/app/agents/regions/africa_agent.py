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


class AfricaGeoAgent(GeoAgent):
    """Africa geo-agent focused on Cape of Good Hope and sub-Saharan ports."""

    REGION_ID = "africa"
    REGION_NAME = "Africa / Cape of Good Hope"
    BBOX = (-10.0, -40.0, 55.0, 5.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
        cape_route_weight: float = 1.5,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )
        self.cape_route_weight = cape_route_weight

    def get_system_prompt(self) -> str:
        """Return Africa operational context for risk reasoning."""
        return (
            "You are Geo-Agent #08 for Africa and the Cape of Good Hope region. "
            "Prioritize risk assessment for Cape Town, Durban, and the critical Cape route "
            "that serves as the primary alternative when Suez disruptions occur. "
            "Critical context: Cape route adds 10-14 days sailing time vs Suez, "
            "South African port capacity constraints, seasonal winter storm exposure (May-August), "
            "Indian Ocean cyclone threats to East African ports, and hinterland logistics "
            "fragility from rail and road infrastructure limitations. "
            "Elevate risk signals when global Suez disruptions redirect traffic burden toward "
            "Cape capacity, or when Durban/Cape Town face simultaneous operational stress."
        )

    async def reason(
        self, events: list[Event], perception_result: PerceptionResult | None = None
    ) -> Decision:
        """Attach Cape route alternative weight and capacity metadata to the assessment."""
        decision = await super().reason(events, perception_result)
        decision["cape_route_weight"] = self.cape_route_weight
        decision["suez_alternate_sensitivity"] = "active"
        return decision
