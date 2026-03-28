from __future__ import annotations

from app.agents.base_agent import Decision, Event, GeoAgent, PerceptionResult


class GulfSuezGeoAgent(GeoAgent):
    """High-sensitivity geo-agent for Red Sea, Suez Canal, and Persian Gulf."""

    REGION_ID = "gulf_suez"
    REGION_NAME = "Gulf / Suez Risk Corridor"
    BBOX = (32.0, 10.0, 60.0, 30.0)

    def __init__(
        self,
        llm_client: object,
        zep_client: object,
        poll_interval_seconds: int = 60,
        confidence_threshold: float = 0.6,
        gdelt_political_weight: float = 2.0,
    ) -> None:
        super().__init__(
            region_id=self.REGION_ID,
            region_name=self.REGION_NAME,
            bbox=self.BBOX,
            llm_client=llm_client,
            zep_client=zep_client,
            poll_interval_seconds=poll_interval_seconds,
        )
        self.confidence_threshold = confidence_threshold
        self.gdelt_political_weight = gdelt_political_weight

    def get_system_prompt(self) -> str:
        """Return elevated-risk geopolitical context for Gulf/Suez reasoning."""
        return (
            "You are Geo-Agent #03 for the Gulf/Suez corridor. "
            "This is a high-stakes region spanning the Red Sea, Suez Canal, and Persian Gulf. "
            "Prioritize risk around Suez throughput (about 12% of global trade), Bab-el-Mandeb chokepoint "
            "exposure, Houthi threat-zone escalation, and historical closure patterns including Ever Given (2021). "
            "Apply 2x sensitivity to geopolitical intensity signals from GDELT and bias toward earlier warnings "
            "when multi-source indicators align."
        )

    async def reason(
        self, events: list[Event], perception_result: PerceptionResult | None = None
    ) -> Decision:
        """Attach corridor-specific sensitivity metadata to the assessment output."""
        decision = await super().reason(events, perception_result)
        decision["confidence_threshold"] = self.confidence_threshold
        decision["gdelt_political_weight"] = self.gdelt_political_weight
        decision["alert_sensitivity"] = "elevated"
        return decision
