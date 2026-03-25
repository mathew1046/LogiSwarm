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
