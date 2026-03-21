from __future__ import annotations

import os
import random
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VesselPosition


class AisVesselSnapshot(BaseModel):
    """Normalized AIS vessel position schema."""

    model_config = ConfigDict(extra="allow")

    vessel_id: str
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    speed: float | None = None
    heading: float | None = Field(default=None, ge=0.0, le=360.0)
    status: str
    timestamp: datetime


class AisConnector:
    """Poll AIS data from provider API or generate deterministic mock snapshots in dev."""

    def __init__(self, poll_interval_seconds: int = 300) -> None:
        self.poll_interval_seconds = int(
            os.getenv("AIS_POLL_INTERVAL_SECONDS", poll_interval_seconds)
        )
        self.provider_url = os.getenv("AIS_PROVIDER_URL", "").strip()
        self.provider_api_key = os.getenv("AIS_PROVIDER_API_KEY", "").strip()

    async def poll(
        self,
        bbox: tuple[float, float, float, float],
        session: AsyncSession,
    ) -> list[AisVesselSnapshot]:
        """Poll snapshots for a bbox and persist raw positions to TimescaleDB."""
        snapshots = await self.fetch_positions(bbox)
        await self.store_snapshots(session=session, snapshots=snapshots)
        return snapshots

    async def fetch_positions(
        self,
        bbox: tuple[float, float, float, float],
    ) -> list[AisVesselSnapshot]:
        """Fetch AIS snapshots from configured API or fallback mock generator."""
        if self.provider_url:
            try:
                return await self._fetch_from_provider(bbox)
            except Exception:
                # Dev-friendly fallback when provider is unavailable.
                return self._mock_snapshots(bbox)

        return self._mock_snapshots(bbox)

    async def _fetch_from_provider(
        self,
        bbox: tuple[float, float, float, float],
    ) -> list[AisVesselSnapshot]:
        params = {"bbox": ",".join(str(v) for v in bbox)}
        headers = {"Accept": "application/json"}
        if self.provider_api_key:
            headers["Authorization"] = f"Bearer {self.provider_api_key}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(self.provider_url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        items: list[dict[str, Any]]
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = payload.get("data") or payload.get("vessels") or []
        else:
            items = []

        snapshots: list[AisVesselSnapshot] = []
        for item in items:
            snapshots.append(
                AisVesselSnapshot(
                    vessel_id=str(item.get("vessel_id") or item.get("mmsi") or item.get("imo")),
                    lat=float(item.get("lat")),
                    lon=float(item.get("lon")),
                    speed=float(item["speed"]) if item.get("speed") is not None else None,
                    heading=float(item["heading"]) if item.get("heading") is not None else None,
                    status=str(item.get("status") or "UNKNOWN"),
                    timestamp=self._parse_timestamp(item.get("timestamp")),
                )
            )
        return snapshots

    def _mock_snapshots(
        self,
        bbox: tuple[float, float, float, float],
        count: int = 25,
    ) -> list[AisVesselSnapshot]:
        min_lon, min_lat, max_lon, max_lat = bbox
        now = datetime.now(UTC)

        snapshots: list[AisVesselSnapshot] = []
        for _ in range(count):
            vessel_token = uuid4().hex[:12]
            snapshots.append(
                AisVesselSnapshot(
                    vessel_id=f"mock-{vessel_token}",
                    lat=round(random.uniform(min_lat, max_lat), 6),
                    lon=round(random.uniform(min_lon, max_lon), 6),
                    speed=round(random.uniform(0.0, 22.0), 2),
                    heading=round(random.uniform(0.0, 360.0), 2),
                    status=random.choice(
                        [
                            "UNDERWAY",
                            "AT_ANCHOR",
                            "MOORED",
                            "CONSTRAINED_BY_DRAFT",
                        ]
                    ),
                    timestamp=now,
                )
            )

        return snapshots

    async def store_snapshots(
        self,
        session: AsyncSession,
        snapshots: list[AisVesselSnapshot],
    ) -> None:
        """Persist raw AIS snapshots into vessel_positions hypertable."""
        if not snapshots:
            return

        for snapshot in snapshots:
            session.add(
                VesselPosition(
                    vessel_id=snapshot.vessel_id,
                    lat=snapshot.lat,
                    lon=snapshot.lon,
                    speed=snapshot.speed,
                    heading=snapshot.heading,
                    status=snapshot.status,
                    timestamp=snapshot.timestamp,
                    raw=snapshot.model_dump(mode="json"),
                )
            )

        await session.commit()

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str) and value:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = datetime.now(UTC)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
