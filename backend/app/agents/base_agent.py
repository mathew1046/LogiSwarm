from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from typing import Any

from loguru import logger

from app.agents.prompt_builder import AgentPromptBuilder
from app.bus.channels import alert_channel
from app.bus.publisher import publish
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
        self._stop_event = asyncio.Event()

        self.last_events: list[Event] = []
        self.last_decision: Decision | None = None
        self.last_cycle_at: datetime | None = None

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return region-specific system instructions for reasoning."""

    async def perceive(self, lookback_minutes: int = 60) -> list[Event]:
        """Fetch normalized events for this region using the feed aggregator."""
        events = await self.aggregator.get_region_events(
            region_id=self.region_id,
            lookback_minutes=lookback_minutes,
        )
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
        return await self.bus(channel, decision)

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

    async def stop(self) -> None:
        """Stop the agent loop and await task cancellation/termination."""
        self._stop_event.set()
        if self._task is None:
            return

        try:
            await self._task
        finally:
            self._task = None

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
        return []

    @staticmethod
    def _build_anomaly_description(events: list[Event]) -> str:
        if not events:
            return "No active event signals"
        top_signals = [f"{event.source}:{event.event_type}:{event.severity}" for event in events[:6]]
        return " | ".join(top_signals)

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
