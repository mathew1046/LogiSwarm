from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from app.feeds.ais_connector import AisConnector, AisVesselSnapshot
from app.feeds.carrier_connector import CarrierConnector, CarrierShipmentUpdate
from app.feeds.gdelt_connector import GdeltConnector, GdeltRiskEvent
from app.feeds.port_simulator import PortSensorSimulator, PortSensorSnapshot
from app.feeds.weather_connector import WeatherConnector, WeatherEvent


DEFAULT_BBOX_BY_REGION: dict[str, tuple[float, float, float, float]] = {
    "se_asia": (92.0, -10.0, 142.0, 25.0),
    "europe": (-10.0, 35.0, 30.0, 65.0),
    "gulf_suez": (32.0, 10.0, 60.0, 30.0),
    "north_america": (-130.0, 20.0, -60.0, 55.0),
    "china_ea": (100.0, 18.0, 145.0, 45.0),
}


SEVERITY_ORDER = {
    "CRITICAL": 5,
    "HIGH_RISK": 4,
    "HIGH": 3,
    "DELAY_ALERT": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


class Event(BaseModel):
    """Unified event format consumed by geo-agents during perception."""

    model_config = ConfigDict(extra="allow")

    source: str
    event_type: str
    severity: str
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    timestamp: datetime
    raw: dict


class FeedAggregator:
    """Aggregate heterogeneous connector payloads into a single normalized event stream."""

    def __init__(self) -> None:
        self.ais_connector = AisConnector()
        self.weather_connector = WeatherConnector()
        self.port_simulator = PortSensorSimulator()
        self.carrier_connector = CarrierConnector()
        self.gdelt_connector = GdeltConnector()

    async def get_region_events(
        self,
        region_id: str,
        lookback_minutes: int = 60,
    ) -> list[Event]:
        """Collect, deduplicate, and sort region events across all feed connectors."""
        bbox = self._resolve_bbox(region_id)

        source_results = await asyncio.gather(
            self._from_ais(bbox=bbox),
            self._from_weather(region_id=region_id, bbox=bbox),
            self._from_port(region_id=region_id, bbox=bbox),
            self._from_carrier(region_id=region_id, bbox=bbox),
            self._from_gdelt(region_id=region_id, bbox=bbox),
            return_exceptions=True,
        )

        merged: list[Event] = []
        for result in source_results:
            if isinstance(result, Exception):
                continue
            merged.extend(result)

        deduped = self._dedupe(merged)
        filtered = self._filter_lookback(deduped, lookback_minutes=lookback_minutes)
        return sorted(
            filtered,
            key=lambda event: (
                -SEVERITY_ORDER.get(event.severity.upper(), 0),
                -event.timestamp.timestamp(),
            ),
        )

    async def _from_ais(self, bbox: tuple[float, float, float, float]) -> list[Event]:
        snapshots = await self.ais_connector.fetch_positions(bbox=bbox)
        events: list[Event] = []
        for snapshot in snapshots:
            events.append(
                Event(
                    source="ais",
                    event_type="VESSEL_POSITION",
                    severity="LOW",
                    lat=snapshot.lat,
                    lon=snapshot.lon,
                    timestamp=snapshot.timestamp,
                    raw=snapshot.model_dump(mode="json"),
                )
            )
        return events

    async def _from_weather(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[Event]:
        weather_events = await self.weather_connector.fetch(region_id=region_id, bbox=bbox)
        events: list[Event] = []
        for item in weather_events:
            events.append(
                Event(
                    source="weather",
                    event_type=item.alert_type,
                    severity=item.severity,
                    lat=item.lat,
                    lon=item.lon,
                    timestamp=item.valid_from,
                    raw=item.model_dump(mode="json"),
                )
            )
        return events

    async def _from_port(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[Event]:
        snapshots = await self.port_simulator.fetch(region_id=region_id)
        center_lat, center_lon = self._bbox_center(bbox)
        events: list[Event] = []

        for item in snapshots:
            severity = "HIGH" if item.anomaly_type else "LOW"
            event_type = item.anomaly_type or "PORT_STATUS"
            events.append(
                Event(
                    source="port_simulator",
                    event_type=event_type,
                    severity=severity,
                    lat=center_lat,
                    lon=center_lon,
                    timestamp=item.timestamp,
                    raw=item.model_dump(mode="json"),
                )
            )

        return events

    async def _from_carrier(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[Event]:
        center_lat, center_lon = self._bbox_center(bbox)

        # Task 012 keeps this connector integration minimal until shipment registry API lands.
        shipment_ids = [f"{region_id}-demo-shipment-001", f"{region_id}-demo-shipment-002"]

        updates = await self.carrier_connector.fetch_shipments(shipment_ids=shipment_ids, carrier="maersk")
        events: list[Event] = []
        for item in updates:
            event_type = "DELAY_ALERT" if item.delay_hours > 24 else "SHIPMENT_STATUS"
            severity = self._carrier_severity(item)
            events.append(
                Event(
                    source="carrier",
                    event_type=event_type,
                    severity=severity,
                    lat=center_lat,
                    lon=center_lon,
                    timestamp=item.eta,
                    raw=item.model_dump(mode="json"),
                )
            )

        return events

    async def _from_gdelt(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[Event]:
        gdelt_events = await self.gdelt_connector.fetch(region_id=region_id, bbox=bbox)
        center_lat, center_lon = self._bbox_center(bbox)
        events: list[Event] = []

        for item in gdelt_events:
            severity = self._gdelt_severity(item)
            events.append(
                Event(
                    source="gdelt",
                    event_type=item.event_type,
                    severity=severity,
                    lat=center_lat,
                    lon=center_lon,
                    timestamp=item.date,
                    raw=item.model_dump(mode="json"),
                )
            )

        return events

    @staticmethod
    def _dedupe(events: list[Event]) -> list[Event]:
        seen: set[tuple[str, str]] = set()
        deduped: list[Event] = []

        for event in events:
            key = (event.source, event.timestamp.isoformat())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(event)

        return deduped

    @staticmethod
    def _filter_lookback(events: list[Event], lookback_minutes: int) -> list[Event]:
        cutoff = datetime.now(UTC) - timedelta(minutes=lookback_minutes)
        return [event for event in events if event.timestamp >= cutoff]

    @staticmethod
    def _carrier_severity(item: CarrierShipmentUpdate) -> str:
        if item.delay_hours > 24:
            return "HIGH"
        if item.customs_hold or item.delay_hours > 6:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _gdelt_severity(item: GdeltRiskEvent) -> str:
        if item.event_type == "RISK_SIGNAL" or item.intensity_score >= 70:
            return "HIGH"
        if item.intensity_score >= 35:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _resolve_bbox(region_id: str) -> tuple[float, float, float, float]:
        return DEFAULT_BBOX_BY_REGION.get(region_id, (-180.0, -85.0, 180.0, 85.0))

    @staticmethod
    def _bbox_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        return center_lat, center_lon
