from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.bus.channels import alert_channel
from app.bus.publisher import publish
from app.feeds.aggregator import Event, FeedAggregator


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
    ) -> None:
        self.region_id = region_id
        self.region_name = region_name
        self.bbox = bbox
        self.llm_client = llm_client
        self.zep_client = zep_client
        self.bus = bus or publish

        self.poll_interval_seconds = poll_interval_seconds
        self.aggregator = aggregator or FeedAggregator()

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
        payload = {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "system_prompt": self.get_system_prompt(),
            "events": [event.model_dump(mode="json") for event in events],
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
