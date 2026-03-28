from __future__ import annotations

from app.agents.base_agent import Decision, Event, GeoAgent, PerceptionResult


class SEAsiaGeoAgent(GeoAgent):
    """Southeast Asia geo-agent focused on Malacca chokepoint disruption risk."""

    REGION_ID = "se_asia"
    REGION_NAME = "Southeast Asia / Strait of Malacca"
    BBOX = (92.0, -10.0, 142.0, 25.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
        ais_expected_vessel_count: int = 500,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )
        self.ais_expected_vessel_count = ais_expected_vessel_count
        self.last_ais_vessel_count = 0
        self._historical_seeded = False

    def get_system_prompt(self) -> str:
        """Return Southeast Asia operational context for risk reasoning."""
        return (
            "You are Geo-Agent #01 for Southeast Asia and the Strait of Malacca. "
            "Prioritize chokepoint resilience and identify disruptions before cascade effects spread. "
            "Critical context: Strait of Malacca traffic concentration, Port of Singapore, Port Klang, "
            "monsoon-season risk windows (October-January), and piracy risk zones along high-density lanes. "
            "Treat sustained AIS congestion and weather-linked throughput degradation as early-warning signals "
            "that can impact Asia-Europe trade corridors."
        )

    async def perceive(self, lookback_minutes: int = 60) -> PerceptionResult:
        """Fetch events and retain AIS vessel-volume signal for decision context."""
        result = await super().perceive(lookback_minutes=lookback_minutes)
        self.last_ais_vessel_count = len(
            [e for e in result.events if e.source == "ais"]
        )
        return result

    async def reason(
        self, events: list[Event], perception_result: PerceptionResult | None = None
    ) -> Decision:
        """Include AIS vessel load context with the LLM assessment output."""
        decision = await super().reason(events, perception_result)
        decision["ais_vessel_count_observed"] = self.last_ais_vessel_count
        decision["ais_vessel_count_expected"] = self.ais_expected_vessel_count
        decision["ais_subscription"] = "active"
        return decision

    async def start(self) -> None:
        """Seed region-specific history once, then start the agent loop."""
        if not self._historical_seeded:
            await self._seed_historical_memory()
            self._historical_seeded = True
        await super().start()

    async def _seed_historical_memory(self) -> None:
        if not hasattr(self.zep_client, "write_resolved_episode"):
            return

        await self.zep_client.write_resolved_episode(
            region_id=self.region_id,
            severity="HIGH",
            duration_hours=72.0,
            resolution="Staggered departures and corridor balancing reduced queue pressure",
            episode_summary=(
                "Suez-equivalent crowding pressure propagated into Malacca approaches with elevated anchorage "
                "queues and schedule compression across transshipment hubs."
            ),
        )
        await self.zep_client.write_resolved_episode(
            region_id=self.region_id,
            severity="CRITICAL",
            duration_hours=168.0,
            resolution="Phased port reopening and berth-priority policy restored vessel flow",
            episode_summary=(
                "COVID-era shutdown constraints at major Southeast Asian ports created prolonged dwell-time surges "
                "and feeder service instability."
            ),
        )
