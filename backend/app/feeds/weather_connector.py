from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.bus.connection import get_redis_client


HIGH_RISK_KEYWORDS = {"storm", "cyclone", "fog", "blizzard"}


class WeatherEvent(BaseModel):
    """Normalized weather event schema for geo-agent consumption."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    alert_type: str
    severity: str
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    valid_from: datetime
    valid_to: datetime


class WeatherConnector:
    """Fetch weather alerts/forecast signals and cache normalized events in Redis."""

    def __init__(self, cache_ttl_seconds: int = 900) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds

    async def fetch(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[WeatherEvent]:
        """Get normalized weather events, using Redis cache with a 15-minute TTL."""
        cache_key = self._cache_key(region_id, bbox)
        cached_events = await self._read_cache(cache_key)
        if cached_events is not None:
            return cached_events

        events: list[WeatherEvent]
        if self._is_us_bbox(bbox):
            events = await self._fetch_noaa(region_id, bbox)
        else:
            events = await self._fetch_open_meteo(region_id, bbox)

        if not events:
            events = self._mock_events(region_id, bbox)

        await self._write_cache(cache_key, events)
        return events

    async def _fetch_noaa(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[WeatherEvent]:
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        url = "https://api.weather.gov/alerts/active"
        params = {"point": f"{center_lat},{center_lon}"}
        headers = {
            "Accept": "application/geo+json",
            "User-Agent": "LogiSwarm/0.1 (ops@logiswarm.local)",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        features = payload.get("features", []) if isinstance(payload, dict) else []
        events: list[WeatherEvent] = []

        for feature in features:
            properties = feature.get("properties") or {}
            geometry = feature.get("geometry") or {}
            coordinates = self._extract_lon_lat(geometry) or (center_lon, center_lat)
            alert_type = str(properties.get("event") or "WEATHER_ALERT")
            severity = self._normalize_severity(
                alert_type=alert_type,
                severity_hint=properties.get("severity"),
            )
            valid_from = self._parse_datetime(properties.get("onset") or properties.get("effective"))
            valid_to = self._parse_datetime(properties.get("ends") or properties.get("expires"))
            if valid_to < valid_from:
                valid_to = valid_from + timedelta(hours=6)

            events.append(
                WeatherEvent(
                    region_id=region_id,
                    alert_type=alert_type,
                    severity=severity,
                    lat=coordinates[1],
                    lon=coordinates[0],
                    valid_from=valid_from,
                    valid_to=valid_to,
                )
            )

        return events

    async def _fetch_open_meteo(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[WeatherEvent]:
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": center_lat,
            "longitude": center_lon,
            "hourly": "weather_code,visibility,windspeed_10m",
            "forecast_days": 1,
            "timezone": "UTC",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        hourly = payload.get("hourly") if isinstance(payload, dict) else None
        if not isinstance(hourly, dict):
            return []

        times = hourly.get("time") or []
        weather_codes = hourly.get("weather_code") or []
        visibilities = hourly.get("visibility") or []
        wind_speeds = hourly.get("windspeed_10m") or []

        events: list[WeatherEvent] = []
        for idx, ts in enumerate(times[:8]):
            code = weather_codes[idx] if idx < len(weather_codes) else None
            visibility = visibilities[idx] if idx < len(visibilities) else None
            wind = wind_speeds[idx] if idx < len(wind_speeds) else None

            alert_type = self._open_meteo_alert_type(code=code, visibility=visibility, wind=wind)
            if alert_type is None:
                continue

            valid_from = self._parse_datetime(ts)
            valid_to = valid_from + timedelta(hours=1)
            severity = self._normalize_severity(alert_type=alert_type, severity_hint=None)

            events.append(
                WeatherEvent(
                    region_id=region_id,
                    alert_type=alert_type,
                    severity=severity,
                    lat=center_lat,
                    lon=center_lon,
                    valid_from=valid_from,
                    valid_to=valid_to,
                )
            )

        return events

    def _mock_events(
        self,
        region_id: str,
        bbox: tuple[float, float, float, float],
    ) -> list[WeatherEvent]:
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        now = datetime.now(UTC)

        return [
            WeatherEvent(
                region_id=region_id,
                alert_type="FOG_ADVISORY",
                severity="HIGH_RISK",
                lat=center_lat,
                lon=center_lon,
                valid_from=now,
                valid_to=now + timedelta(hours=3),
            )
        ]

    @staticmethod
    def _open_meteo_alert_type(code: Any, visibility: Any, wind: Any) -> str | None:
        code_int = int(code) if code is not None else -1
        vis = float(visibility) if visibility is not None else None
        wind_speed = float(wind) if wind is not None else None

        # WMO weather code mapping (simplified for risk-oriented classification)
        if code_int in {95, 96, 99}:
            return "STORM_THUNDER"
        if code_int in {71, 73, 75, 77, 85, 86}:
            return "BLIZZARD_CONDITIONS"
        if code_int in {61, 63, 65, 80, 81, 82} and wind_speed is not None and wind_speed > 55:
            return "CYCLONE_LIKE_RAIN_BAND"
        if vis is not None and vis < 500:
            return "FOG_DENSE"
        return None

    @staticmethod
    def _normalize_severity(alert_type: str, severity_hint: Any) -> str:
        if any(keyword in alert_type.lower() for keyword in HIGH_RISK_KEYWORDS):
            return "HIGH_RISK"

        normalized_hint = str(severity_hint or "").strip().lower()
        if normalized_hint in {"extreme", "severe", "major"}:
            return "HIGH"
        if normalized_hint in {"moderate"}:
            return "MEDIUM"
        if normalized_hint:
            return "LOW"
        return "MEDIUM"

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str) and value:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = datetime.now(UTC)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @staticmethod
    def _is_us_bbox(bbox: tuple[float, float, float, float]) -> bool:
        min_lon, min_lat, max_lon, max_lat = bbox
        return min_lon >= -170 and max_lon <= -50 and min_lat >= 15 and max_lat <= 75

    @staticmethod
    def _cache_key(region_id: str, bbox: tuple[float, float, float, float]) -> str:
        parts = ",".join(f"{value:.4f}" for value in bbox)
        return f"weather:events:{region_id}:{parts}"

    async def _read_cache(self, key: str) -> list[WeatherEvent] | None:
        client = get_redis_client()
        try:
            payload = await client.get(key)
            if not payload:
                return None

            items = json.loads(payload)
            return [WeatherEvent.model_validate(item) for item in items]
        finally:
            await client.aclose()

    async def _write_cache(self, key: str, events: list[WeatherEvent]) -> None:
        client = get_redis_client()
        try:
            payload = json.dumps([event.model_dump(mode="json") for event in events])
            await client.setex(key, self.cache_ttl_seconds, payload)
        finally:
            await client.aclose()

    @staticmethod
    def _extract_lon_lat(geometry: dict[str, Any]) -> tuple[float, float] | None:
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if not geom_type or coordinates is None:
            return None

        if geom_type == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
            return float(coordinates[0]), float(coordinates[1])

        if geom_type in {"Polygon", "MultiPolygon"}:
            first = WeatherConnector._first_coordinate(coordinates)
            if first and len(first) >= 2:
                return float(first[0]), float(first[1])

        return None

    @staticmethod
    def _first_coordinate(value: Any) -> list[float] | None:
        if isinstance(value, list):
            if value and isinstance(value[0], (int, float)):
                return value
            for item in value:
                found = WeatherConnector._first_coordinate(item)
                if found:
                    return found
        return None
