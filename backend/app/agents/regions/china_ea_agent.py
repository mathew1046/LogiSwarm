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

from app.agents.base_agent import Decision, Event, GeoAgent


class ChinaEastAsiaGeoAgent(GeoAgent):
    """Geo-agent for China/East Asia manufacturing-export corridor risk detection."""

    REGION_ID = "china_ea"
    REGION_NAME = "China / East Asia Export Corridor"
    BBOX = (100.0, 18.0, 145.0, 45.0)

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
        self.last_factory_idle_signals = 0

    def get_system_prompt(self) -> str:
        """Return East Asia export-hub context and manufacturing-cycle risk cues."""
        return (
            "You are Geo-Agent #05 for China/East Asia manufacturing and export flows. "
            "Focus on disruption risk around Port of Shanghai, Ningbo-Zhoushan, and Busan transit operations. "
            "Incorporate production-cycle seasonality including Chinese New Year shutdowns and Golden Week surges. "
            "Use COVID-era zero-policy legacy patterns as analogs for abrupt capacity compression. "
            "Elevate risk when factory sensor idle rates rise or export declaration volume weakens via customs-proxy signals."
        )

    async def perceive(self, lookback_minutes: int = 60) -> "PerceptionResult":
        """Track factory-idle proxies from port simulator anomaly patterns."""
        from app.agents.base_agent import PerceptionResult

        perception_result = await super().perceive(lookback_minutes=lookback_minutes)
        self.last_factory_idle_signals = len(
            [
                event
                for event in perception_result.events
                if event.source == "port_simulator"
                and str(event.event_type).upper()
                in {"CRANE_IDLE_6H", "DWELL_TIME_SURGE"}
            ]
        )
        return perception_result

    async def reason(self, events: list[Event]) -> Decision:
        """Attach factory-idle proxy metadata to support risk explainability."""
        decision = await super().reason(events)
        decision["factory_idle_proxy_signals"] = self.last_factory_idle_signals
        decision["export_declaration_proxy"] = "carrier_and_port_signals"
        return decision
