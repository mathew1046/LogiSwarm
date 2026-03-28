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

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict


SUPPLY_CHAIN_EVENT_TYPES = ("protest", "sanctions", "port closure", "strike")
EVENT_TYPE_KEYWORDS: dict[str, set[str]] = {
    "PROTEST": {"protest", "demonstration", "riot", "unrest"},
    "SANCTIONS": {"sanction", "embargo", "restriction", "blacklist"},
    "PORT_CLOSURE": {"port closure", "harbor closure", "terminal shutdown", "port shutdown"},
    "STRIKE": {"strike", "walkout", "labor action", "industrial action"},
}

# Approximate CAMEO code families used as risk hints in GDELT event records.
PROTEST_CODES = {"14", "145", "172"}
SANCTION_CODES = {"112", "113", "114"}
STRIKE_CODES = {"173", "174"}


class GdeltRiskEvent(BaseModel):
    """Normalized geopolitical event schema from GDELT."""

    model_config = ConfigDict(extra="allow")

    event_type: str
    actor: str
    region: str
    intensity_score: float
    date: datetime


class GdeltConnector:
    """Fetch and normalize supply-chain-relevant geopolitical signals from GDELT."""

    def __init__(
        self,
        base_url: str = "https://api.gdeltproject.org/api/v2/doc/doc",
        timeout_seconds: float = 20.0,
        max_records: int = 50,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.max_records = max_records

    async def fetch(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
        event_types: tuple[str, ...] = SUPPLY_CHAIN_EVENT_TYPES,
    ) -> list[GdeltRiskEvent]:
        """Fetch region-level geopolitical risk events, with a mock fallback for dev resilience."""
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        records: list[dict[str, Any]] = []
        for event_type in event_types:
            try:
                payload = await self._query_gdelt(
                    lat=center_lat,
                    lon=center_lon,
                    event_type=event_type,
                )
                records.extend(self._extract_items(payload))
            except Exception:
                continue

        events = self._normalize(records=records, region_id=region_id)
        if events:
            return events

        return self._mock_events(region_id=region_id)

    async def _query_gdelt(
        self,
        lat: float,
        lon: float,
        event_type: str,
    ) -> dict[str, Any]:
        query = f'"{event_type}" near:{lat:.3f},{lon:.3f},350km'
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": str(self.max_records),
            "sort": "DateDesc",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, dict):
            return {}
        return payload

    @staticmethod
    def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        articles = payload.get("articles")
        if isinstance(articles, list):
            return [item for item in articles if isinstance(item, dict)]

        events = payload.get("events")
        if isinstance(events, list):
            return [item for item in events if isinstance(item, dict)]

        return []

    def _normalize(
        self,
        records: list[dict[str, Any]],
        region_id: str,
    ) -> list[GdeltRiskEvent]:
        normalized: list[GdeltRiskEvent] = []

        for record in records:
            mapped_type = self._map_event_type(record)
            if mapped_type is None:
                continue

            tone = self._parse_tone(record)
            final_type = "RISK_SIGNAL" if tone < -5.0 else mapped_type
            intensity_score = self._compute_intensity_score(record=record, tone=tone)

            normalized.append(
                GdeltRiskEvent(
                    event_type=final_type,
                    actor=self._extract_actor(record),
                    region=region_id,
                    intensity_score=intensity_score,
                    date=self._parse_date(record),
                )
            )

        return normalized

    def _map_event_type(self, record: dict[str, Any]) -> str | None:
        searchable = " ".join(
            [
                str(record.get("title") or ""),
                str(record.get("seendate") or ""),
                str(record.get("sourceCommonName") or ""),
                str(record.get("source_name") or ""),
                str(record.get("theme") or ""),
                str(record.get("themes") or ""),
                str(record.get("eventType") or ""),
            ]
        ).lower()

        for mapped_type, keywords in EVENT_TYPE_KEYWORDS.items():
            if any(keyword in searchable for keyword in keywords):
                return mapped_type

        code = str(
            record.get("eventCode")
            or record.get("EventCode")
            or record.get("eventcode")
            or record.get("eventRootCode")
            or record.get("EventRootCode")
            or ""
        ).strip()
        if code in PROTEST_CODES:
            return "PROTEST"
        if code in SANCTION_CODES:
            return "SANCTIONS"
        if code in STRIKE_CODES:
            return "STRIKE"

        return None

    @staticmethod
    def _compute_intensity_score(record: dict[str, Any], tone: float) -> float:
        mentions = float(record.get("numMentions") or record.get("mentions") or 0.0)
        relevance = float(record.get("relevance") or 0.0)

        score = (abs(tone) * 6.0) + (mentions * 0.15) + (relevance * 10.0)
        return round(max(0.0, min(score, 100.0)), 2)

    @staticmethod
    def _extract_actor(record: dict[str, Any]) -> str:
        return str(
            record.get("actor1name")
            or record.get("actor")
            or record.get("sourceCommonName")
            or record.get("source_name")
            or "UNKNOWN"
        )

    @staticmethod
    def _parse_tone(record: dict[str, Any]) -> float:
        value = record.get("tone")
        if value is None:
            value = record.get("avgTone")
        if value is None:
            value = record.get("toneavg")

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _parse_date(record: dict[str, Any]) -> datetime:
        value = (
            record.get("date")
            or record.get("seendate")
            or record.get("seenDate")
            or record.get("sqlDate")
        )

        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(float(value), tz=UTC)
        elif isinstance(value, str) and value:
            normalized = value.strip().replace("Z", "+00:00")
            dt = GdeltConnector._parse_datetime_from_str(normalized)
        else:
            dt = datetime.now(UTC) - timedelta(hours=1)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @staticmethod
    def _parse_datetime_from_str(value: str) -> datetime:
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y%m%d%H%M%S",
            "%Y%m%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=UTC)
                return dt
            except ValueError:
                continue

        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            return datetime.now(UTC)

    @staticmethod
    def _mock_events(region_id: str) -> list[GdeltRiskEvent]:
        now = datetime.now(UTC)
        return [
            GdeltRiskEvent(
                event_type="RISK_SIGNAL",
                actor="MOCK_LABOR_UNION",
                region=region_id,
                intensity_score=78.5,
                date=now,
            ),
            GdeltRiskEvent(
                event_type="PORT_CLOSURE",
                actor="MOCK_PORT_AUTHORITY",
                region=region_id,
                intensity_score=66.2,
                date=now - timedelta(hours=3),
            ),
        ]
