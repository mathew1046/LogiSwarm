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

from app.agents.base_agent import GeoAgent


class EuropeGeoAgent(GeoAgent):
    """North Europe corridor geo-agent centered on port and inland flow stability."""

    REGION_ID = "europe"
    REGION_NAME = "Europe Logistics Corridor"
    BBOX = (-10.0, 35.0, 30.0, 65.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )

    def get_system_prompt(self) -> str:
        """Return Europe-specific context for disruption assessment."""
        return (
            "You are Geo-Agent #02 for the North Europe logistics corridor. "
            "Track disruption risk across Port of Rotterdam, Hamburg, Antwerp, and Rhine-linked inland flows. "
            "Account for EU customs friction, rail-freight bottlenecks, and intermodal transfer dependencies. "
            "Elevate risk when dock-strike signals rise, Rhine water levels indicate drought constraints, "
            "or truck-driver shortages threaten hinterland evacuation capacity."
        )
