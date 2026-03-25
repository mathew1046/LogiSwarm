from __future__ import annotations

import asyncio
from asyncio import Task
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from typing import Any
from uuid import uuid4

from loguru import logger

from app.agents.prompt_builder import AgentPromptBuilder
from app.bus.channels import alert_channel, broadcast_channel
from app.bus.connection import get_redis_client
from app.bus.publisher import publish
from app.bus.subscriber import subscribe
from app.feeds.aggregator import Event, FeedAggregator

if TYPE_CHECKING:
    from app.agents.memory import MemoryEpisode


Decision = dict[str, Any]
LlmReasonCallable = Callable[[dict[str, Any]], Awaitable[Decision] | Decision]


class GeoAgent(ABC):
    """Base geo-agent implementing the perceive → reason → act lifecycle."""

    def __init__(
        self,
        region_id: str,
        region_name: str,
        bbox: tuple[float, float, float, float],
        llm_client: Any,
        zep_client: Any,
        bus: Callable[[str, dict[str, Any]], Awaitable[int]] | None = None,
        poll_interval_seconds: int = 60,
        aggregator: FeedAggregator | None = None,
        prompt_builder: AgentPromptBuilder | None = None,
    ) -> None:
        self.region_id = region_id
        self.region_name = region_name
        self.bbox = bbox
        self.llm_client = llm_client
        self.zep_client = zep_client
        self.bus = bus or publish

        self.poll_interval_seconds = poll_interval_seconds
        self.aggregator = aggregator or FeedAggregator()
        self.prompt_builder = prompt_builder or AgentPromptBuilder()

        self._task: asyncio.Task[None] | None = None
        self._broadcast_listener_task: Task[None] | None = None
        self._stop_event = asyncio.Event()

        self.last_events: list[Event] = []
        self.last_decision: Decision | None = None
        self.last_cycle_at: datetime | None = None
        self.neighbor_region_ids: list[str] = []
        self._incoming_neighbor_signals: list[dict[str, Any]] = []

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return region-specific system instructions for reasoning."""

    async def perceive(self, lookback_minutes: int = 60) -> list[Event]:
        """Fetch normalized events for this region using the feed aggregator."""
        events = await self.aggregator.get_region_events(
            region_id=self.region_id,
            lookback_minutes=lookback_minutes,
        )
        events.extend(self._neighbor_signal_events())
        self.last_events = events
        return events

    async def reason(self, events: list[Event]) -> Decision:
        """Run LLM reasoning over current events and memory context."""
        memory_episodes = await self._retrieve_memory_episodes(events)
        memory_lines = self._format_memory_lines(memory_episodes)
        recent_resolved_lines = self._recent_resolved_lines(memory_episodes)
        neighbor_alert_lines = self._neighbor_alert_lines()

        dynamic_system_prompt = self.prompt_builder.build_prompt(
            base_prompt=self.get_system_prompt(),
            memory_lines=memory_lines,
            recent_resolved_lines=recent_resolved_lines,
            neighbor_alert_lines=neighbor_alert_lines,
        )

        payload = {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "system_prompt": dynamic_system_prompt,
            "events": [event.model_dump(mode="json") for event in events],
            "memory_episodes": [
                self._episode_to_payload(episode) for episode in memory_episodes
            ],
        }

        if hasattr(self.llm_client, "reason"):
            result = self.llm_client.reason(payload)
            decision = await result if asyncio.iscoroutine(result) else result
        elif callable(self.llm_client):
            result = self.llm_client(payload)
            decision = await result if asyncio.iscoroutine(result) else result
        else:
            decision = {
                "severity": "LOW",
                "confidence": 0.0,
                "recommended_actions": [],
                "reasoning": "LLM client not configured",
            }

        if not isinstance(decision, dict):
            decision = {
                "severity": "LOW",
                "confidence": 0.0,
                "recommended_actions": [],
                "reasoning": "Invalid LLM decision format",
                "raw": str(decision),
            }

        decision.setdefault("region_id", self.region_id)
        decision.setdefault("region_name", self.region_name)
        decision.setdefault("timestamp", datetime.now(UTC).isoformat())
        self.last_decision = decision
        return decision

    async def act(self, decision: Decision) -> int:
        """Publish the current decision into the region alert channel."""
        channel = alert_channel(self.region_id)
        delivered = await self.bus(channel, decision)
        severity = str(decision.get("severity") or "").upper()
        if severity in {"HIGH", "CRITICAL"}:
            await self.broadcast_to_neighbors(decision)
        return delivered

    async def broadcast_to_neighbors(self, event: dict[str, Any]) -> int:
        """Broadcast high-severity events to neighboring geo-agents."""
        if not self.neighbor_region_ids:
            return 0

        broadcast_id = str(event.get("broadcast_id") or uuid4())
        dedupe_key = f"broadcast:dedupe:{broadcast_id}"
        if not await self._acquire_broadcast_dedupe(dedupe_key):
            return 0

        payload = {
            **event,
            "broadcast_id": broadcast_id,
            "origin_region_id": self.region_id,
            "broadcast_at": datetime.now(UTC).isoformat(),
        }

        delivered = 0
        for neighbor_region_id in self.neighbor_region_ids:
            delivered += await self.bus(broadcast_channel(neighbor_region_id), payload)
        return delivered

    def set_neighbors(self, neighbor_region_ids: list[str]) -> None:
        """Configure neighboring regions used for cross-agent propagation."""
        self.neighbor_region_ids = [region for region in neighbor_region_ids if region != self.region_id]

    async def run_cycle(self) -> Decision:
        """Execute one complete perceive → reason → act cycle."""
        events = await self.perceive()
        decision = await self.reason(events)
        await self.act(decision)
        self.last_cycle_at = datetime.now(UTC)
        return decision

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_cycle()
            except Exception as exc:
                logger.bind(region_id=self.region_id).exception(
                    "Agent cycle failed: {error}",
                    error=str(exc),
                )

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.poll_interval_seconds,
                )
            except asyncio.TimeoutError:
                continue

    async def start(self) -> None:
        """Start the periodic agent loop as a background asyncio task."""
        if self._task and not self._task.done():
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._run(),
            name=f"geo-agent-{self.region_id}",
        )
        self._broadcast_listener_task = asyncio.create_task(
            self._listen_for_neighbor_broadcasts(),
            name=f"geo-agent-broadcast-listener-{self.region_id}",
        )

    async def stop(self) -> None:
        """Stop the agent loop and await task cancellation/termination."""
        self._stop_event.set()
        if self._broadcast_listener_task is not None:
            self._broadcast_listener_task.cancel()
            try:
                await self._broadcast_listener_task
            except asyncio.CancelledError:
                pass
            finally:
                self._broadcast_listener_task = None

        if self._task is None:
            return

        try:
            await self._task
        finally:
            self._task = None

    async def _listen_for_neighbor_broadcasts(self) -> None:
        """Subscribe to this region's broadcast channel and queue incoming signals."""
        channel = broadcast_channel(self.region_id)

        async def _handler(payload: dict[str, Any]) -> None:
            signal = payload if isinstance(payload, dict) else {"raw": payload}
            signal.setdefault("received_at", datetime.now(UTC).isoformat())
            self._incoming_neighbor_signals.append(signal)
            self._incoming_neighbor_signals = self._incoming_neighbor_signals[-50:]

        try:
            await subscribe(channel, _handler)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.bind(region_id=self.region_id).exception(
                "Broadcast listener failed: {error}",
                error=str(exc),
            )

    def _neighbor_signal_events(self) -> list[Event]:
        if not self._incoming_neighbor_signals:
            return []

        center_lat = (self.bbox[1] + self.bbox[3]) / 2
        center_lon = (self.bbox[0] + self.bbox[2]) / 2

        signals = self._incoming_neighbor_signals
        self._incoming_neighbor_signals = []

        events: list[Event] = []
        for signal in signals:
            timestamp = self._parse_datetime(signal.get("broadcast_at") or signal.get("received_at"))
            event_type = f"NEIGHBOR_ALERT_{str(signal.get('origin_region_id') or 'unknown').upper()}"
            events.append(
                Event(
                    source="neighbor_broadcast",
                    event_type=event_type,
                    severity=str(signal.get("severity") or "MEDIUM"),
                    lat=center_lat,
                    lon=center_lon,
                    timestamp=timestamp,
                    raw=signal,
                )
            )
        return events

    async def _retrieve_memory_episodes(self, events: list[Event]) -> list[MemoryEpisode]:
        if not hasattr(self.zep_client, "search_similar_episodes"):
            return []

        anomaly_description = self._build_anomaly_description(events)
        try:
            result = await self.zep_client.search_similar_episodes(
                region_id=self.region_id,
                anomaly_description=anomaly_description,
                top_k=3,
            )
        except Exception:
            return []

        return result if isinstance(result, list) else []

    def _format_memory_lines(self, episodes: list[MemoryEpisode]) -> list[str]:
        if hasattr(self.zep_client, "format_few_shot_context"):
            try:
                lines = self.zep_client.format_few_shot_context(episodes)
                if isinstance(lines, list):
                    return [str(line) for line in lines]
            except Exception:
                pass

        lines: list[str] = []
        for episode in episodes:
            lines.append(
                f"Similar past event [{episode.created_at.date().isoformat()}]: {episode.content} "
                f"→ Outcome: {episode.metadata.resolution}"
            )
        return lines

    @staticmethod
    def _recent_resolved_lines(episodes: list[MemoryEpisode]) -> list[str]:
        cutoff = datetime.now(UTC).replace(microsecond=0)
        lines: list[str] = []
        for episode in episodes:
            age_days = (cutoff - episode.created_at).days
            if age_days <= 30:
                lines.append(
                    f"{episode.created_at.date().isoformat()} | {episode.metadata.severity} | {episode.content}"
                )
        return lines

    def _neighbor_alert_lines(self) -> list[str]:
        lines: list[str] = []
        for signal in self._incoming_neighbor_signals[-10:]:
            lines.append(
                f"{signal.get('origin_region_id', 'unknown')} severity={signal.get('severity', 'MEDIUM')} "
                f"reason={signal.get('reasoning', 'n/a')}"
            )
        return lines

    async def _acquire_broadcast_dedupe(self, key: str) -> bool:
        try:
            client = get_redis_client()
        except Exception:
            return True

        try:
            acquired = await client.set(key, "1", ex=3600, nx=True)
            return bool(acquired)
        except Exception:
            return True
        finally:
            await client.aclose()

    @staticmethod
    def _build_anomaly_description(events: list[Event]) -> str:
        if not events:
            return "No active event signals"
        top_signals = [f"{event.source}:{event.event_type}:{event.severity}" for event in events[:6]]
        return " | ".join(top_signals)

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
    def _episode_to_payload(episode: MemoryEpisode) -> dict[str, Any]:
        return {
            "episode_id": episode.episode_id,
            "content": episode.content,
            "metadata": {
                "region_id": episode.metadata.region_id,
                "severity": episode.metadata.severity,
                "duration_hours": episode.metadata.duration_hours,
                "resolution": episode.metadata.resolution,
            },
            "created_at": episode.created_at.isoformat(),
        }
