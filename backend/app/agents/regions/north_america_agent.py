from __future__ import annotations

from app.agents.base_agent import Decision, Event, GeoAgent


class NorthAmericaGeoAgent(GeoAgent):
    """Geo-agent for US intermodal and port logistics risk monitoring."""

    REGION_ID = "north_america"
    REGION_NAME = "North America Intermodal Network"
    BBOX = (-130.0, 20.0, -60.0, 55.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
        carrier_weight: float = 1.5,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )
        self.carrier_weight = carrier_weight
        self.last_carrier_signal_count = 0

    def get_system_prompt(self) -> str:
        """Return US corridor context including weather, labor, and intermodal choke points."""
        return (
            "You are Geo-Agent #04 for the United States intermodal and port network. "
            "Prioritize disruption detection across Port of LA/Long Beach, Chicago rail hub, and the I-95 freight corridor. "
            "Incorporate seasonal weather risk (hurricanes and blizzards), labor volatility (ILWU contract cycles), "
            "and cascading inland congestion from port-side delays. "
            "Weight carrier API delay/customs signals heavily because US carrier integrations are high-coverage and near real-time."
        )

    async def perceive(self, lookback_minutes: int = 60) -> list[Event]:
        """Track carrier signal volume to weight risk interpretation in the reasoning phase."""
        events = await super().perceive(lookback_minutes=lookback_minutes)
        self.last_carrier_signal_count = len([event for event in events if event.source == "carrier"])
        return events

    async def reason(self, events: list[Event]) -> Decision:
        """Attach carrier-signal weighting metadata to the decision output."""
        decision = await super().reason(events)
        decision["carrier_signal_count"] = self.last_carrier_signal_count
        decision["carrier_signal_weight"] = self.carrier_weight
        return decision
