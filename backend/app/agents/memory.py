from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class EpisodeMetadata(BaseModel):
    """Metadata stored with each episodic memory item."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    severity: str
    duration_hours: float = Field(ge=0.0)
    resolution: str


class MemoryEpisode(BaseModel):
    """Canonical episodic memory record used for storage and retrieval."""

    model_config = ConfigDict(extra="allow")

    episode_id: str
    content: str
    metadata: EpisodeMetadata
    created_at: datetime


class ZepEpisodicMemory:
    """Zep-backed episodic memory service with local fallback for development."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        collection_name: str = "logiswarm-disruptions",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key or os.getenv("ZEP_API_KEY", "")
        self.base_url = (base_url or os.getenv("ZEP_BASE_URL", "https://api.getzep.com")).rstrip("/")
        self.collection_name = collection_name
        self.timeout_seconds = timeout_seconds

        self._local_episodes: list[MemoryEpisode] = []

    async def write_resolved_episode(
        self,
        region_id: str,
        severity: str,
        duration_hours: float,
        resolution: str,
        episode_summary: str,
    ) -> MemoryEpisode:
        """Write a resolved disruption episode into Zep with required metadata."""
        episode = MemoryEpisode(
            episode_id=self._new_episode_id(region_id=region_id),
            content=episode_summary,
            metadata=EpisodeMetadata(
                region_id=region_id,
                severity=severity,
                duration_hours=duration_hours,
                resolution=resolution,
            ),
            created_at=datetime.now(UTC),
        )

        self._local_episodes.append(episode)

        try:
            await self._zep_create_document(episode)
        except Exception:
            # Local cache is maintained as fallback when cloud is unavailable.
            pass

        return episode

    async def search_similar_episodes(
        self,
        region_id: str,
        anomaly_description: str,
        top_k: int = 3,
    ) -> list[MemoryEpisode]:
        """Semantic retrieval for top-k analogous episodes on a new anomaly."""
        cloud_results = await self._zep_search(
            region_id=region_id,
            query=anomaly_description,
            top_k=top_k,
        )
        if cloud_results:
            return cloud_results

        return self._search_local(
            region_id=region_id,
            query=anomaly_description,
            top_k=top_k,
        )

    def format_few_shot_context(self, episodes: list[MemoryEpisode]) -> list[str]:
        """Format retrieved episodes for few-shot insertion into LLM prompts."""
        context: list[str] = []
        for episode in episodes:
            context.append(
                "Similar past event "
                f"[{episode.created_at.date().isoformat()}]: {episode.content} "
                f"→ Outcome: {episode.metadata.resolution}"
            )
        return context

    async def seed_initial_memory(
        self,
        dataset_path: str | None = None,
        region_id: str | None = None,
    ) -> int:
        """Seed memory at startup from a historical disruption dataset (JSON)."""
        seed_rows = await self._load_seed_dataset(dataset_path)
        inserted = 0

        for row in seed_rows:
            row_region = str(row.get("region_id") or "global")
            if region_id and row_region != region_id:
                continue

            summary = str(
                row.get("episode_summary")
                or row.get("summary")
                or row.get("event")
                or "Historical disruption episode"
            )

            await self.write_resolved_episode(
                region_id=row_region,
                severity=str(row.get("severity") or "MEDIUM"),
                duration_hours=float(row.get("duration_hours") or 0.0),
                resolution=str(row.get("resolution") or "Resolved"),
                episode_summary=summary,
            )
            inserted += 1

        return inserted

    async def _zep_create_document(self, episode: MemoryEpisode) -> None:
        if not self.api_key:
            return

        url = f"{self.base_url}/api/v1/collections/{self.collection_name}/documents"
        payload = {
            "document_id": episode.episode_id,
            "content": episode.content,
            "metadata": {
                "region_id": episode.metadata.region_id,
                "severity": episode.metadata.severity,
                "duration_hours": episode.metadata.duration_hours,
                "resolution": episode.metadata.resolution,
                "created_at": episode.created_at.isoformat(),
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()

    async def _zep_search(
        self,
        region_id: str,
        query: str,
        top_k: int,
    ) -> list[MemoryEpisode]:
        if not self.api_key:
            return []

        url = f"{self.base_url}/api/v1/collections/{self.collection_name}/search"
        payload = {
            "query": query,
            "limit": top_k,
            "metadata": {"region_id": region_id},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []

        if not isinstance(data, dict):
            return []

        items = data.get("results") or data.get("matches") or []
        if not isinstance(items, list):
            return []

        episodes: list[MemoryEpisode] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            metadata_raw = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            created_at_raw = metadata_raw.get("created_at") or item.get("created_at")
            created_at = self._parse_datetime(created_at_raw)

            content = str(item.get("content") or item.get("document") or "")
            if not content:
                continue

            episode = MemoryEpisode(
                episode_id=str(item.get("document_id") or item.get("id") or self._new_episode_id(region_id)),
                content=content,
                metadata=EpisodeMetadata(
                    region_id=str(metadata_raw.get("region_id") or region_id),
                    severity=str(metadata_raw.get("severity") or "MEDIUM"),
                    duration_hours=float(metadata_raw.get("duration_hours") or 0.0),
                    resolution=str(metadata_raw.get("resolution") or "Resolved"),
                ),
                created_at=created_at,
            )
            episodes.append(episode)

        return episodes[:top_k]

    def _search_local(self, region_id: str, query: str, top_k: int) -> list[MemoryEpisode]:
        query_terms = self._tokenize(query)
        if not query_terms:
            return [
                episode
                for episode in self._local_episodes
                if episode.metadata.region_id == region_id
            ][:top_k]

        scored: list[tuple[float, MemoryEpisode]] = []
        for episode in self._local_episodes:
            if episode.metadata.region_id != region_id:
                continue

            content_terms = self._tokenize(episode.content)
            if not content_terms:
                continue

            overlap = len(query_terms.intersection(content_terms))
            score = overlap / max(len(query_terms), 1)
            scored.append((score, episode))

        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [episode for _, episode in scored[:top_k]]

    async def _load_seed_dataset(self, dataset_path: str | None) -> list[dict[str, Any]]:
        path = dataset_path or os.getenv("HISTORICAL_DISRUPTIONS_JSON", "")
        if path:
            rows = await asyncio.to_thread(self._read_json_file, path)
            if rows:
                return rows

        return self._default_seed_rows()

    @staticmethod
    def _read_json_file(path: str) -> list[dict[str, Any]]:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)

        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            episodes = payload.get("episodes")
            if isinstance(episodes, list):
                return [item for item in episodes if isinstance(item, dict)]
        return []

    @staticmethod
    def _default_seed_rows() -> list[dict[str, Any]]:
        return [
            {
                "region_id": "gulf_suez",
                "severity": "CRITICAL",
                "duration_hours": 144.0,
                "resolution": "Rerouted via Cape of Good Hope",
                "episode_summary": "Canal blockage created queue build-up and global ripple delays.",
            },
            {
                "region_id": "europe",
                "severity": "HIGH",
                "duration_hours": 36.0,
                "resolution": "Terminal operations resumed after labor agreement",
                "episode_summary": "Dock strike reduced throughput and increased berth waiting times.",
            },
            {
                "region_id": "se_asia",
                "severity": "HIGH",
                "duration_hours": 30.0,
                "resolution": "Weather window reopened and departures normalized",
                "episode_summary": "Monsoon storm cluster disrupted feeder schedules across key transshipment ports.",
            },
        ]

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {
            token.strip(".,:;!?()[]{}\"'").lower()
            for token in text.split()
            if token.strip()
        }

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
    def _new_episode_id(region_id: str) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        return f"{region_id}-{stamp}"
