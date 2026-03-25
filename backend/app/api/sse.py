from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger

from app.bus.channels import (
    ORCHESTRATOR_CASCADE_CHANNEL,
    ORCHESTRATOR_REROUTE_CHANNEL,
    alert_channel,
)
from app.bus.connection import get_redis_client

router = APIRouter(tags=["sse"])

SSE_EVENT_TYPES = {
    "agent_assessment": "agent.*.alert",
    "disruption_detected": ORCHESTRATOR_CASCADE_CHANNEL,
    "cascade_update": ORCHESTRATOR_CASCADE_CHANNEL,
    "route_recommended": ORCHESTRATOR_REROUTE_CHANNEL,
}


class SSEEventBroadcaster:
    """Bridge Redis pub/sub events to SSE stream clients."""

    def __init__(self) -> None:
        self._clients: set[asyncio.Queue[dict[str, Any]]] = set()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """Register a new SSE client and return its event queue."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._clients.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove an SSE client queue."""
        self._clients.discard(queue)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Push an event to all connected SSE clients."""
        for queue in list(self._clients):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    @property
    def client_count(self) -> int:
        return len(self._clients)


sse_broadcaster = SSEEventBroadcaster()


async def sse_event_generator() -> Any:
    """Generate SSE events from Redis pub/sub and broadcast to connected clients."""
    queue = await sse_broadcaster.subscribe()
    client_id = id(queue)

    try:
        yield format_sse_event(
            event_type="connected",
            data={"message": "SSE stream connected", "client_id": client_id},
        )

        client = get_redis_client()
        try:
            pubsub = client.pubsub()
            await pubsub.psubscribe(
                "agent.*.alert",
                ORCHESTRATOR_CASCADE_CHANNEL,
                ORCHESTRATOR_REROUTE_CHANNEL,
            )

            background_task = asyncio.create_task(
                _redis_listener(pubsub, client_id),
                name=f"sse-redis-listener-{client_id}",
            )

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield format_sse_event(
                        event_type=event.get("event_type", "update"),
                        region_id=event.get("region_id"),
                        data=event.get("data", event),
                    )
                except asyncio.TimeoutError:
                    yield format_sse_event(
                        event_type="heartbeat",
                        data={"timestamp": datetime.now(UTC).isoformat()},
                    )

        finally:
            background_task.cancel()
            try:
                await background_task
            except asyncio.CancelledError:
                pass
            await pubsub.aclose()
            await client.aclose()

    finally:
        await sse_broadcaster.unsubscribe(queue)


async def _redis_listener(pubsub: Any, client_id: int) -> None:
    """Listen to Redis pub/sub and forward events to SSE broadcaster."""
    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message.get("type") == "pmessage":
                channel = str(message.get("channel", ""))
                raw_data = message.get("data")
                event = _parse_redis_message(channel, raw_data)
                if event:
                    await sse_broadcaster.broadcast(event)
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.bind(client_id=client_id).error(
            "SSE Redis listener error: {error}", error=str(exc)
        )


def _parse_redis_message(channel: str, raw_data: Any) -> dict[str, Any] | None:
    """Parse a Redis pub/sub message into a structured SSE event."""
    try:
        if isinstance(raw_data, bytes):
            data = json.loads(raw_data.decode("utf-8"))
        elif isinstance(raw_data, str):
            data = json.loads(raw_data)
        elif isinstance(raw_data, dict):
            data = raw_data
        else:
            return None
    except (json.JSONDecodeError, TypeError):
        return None

    event_type = _map_channel_to_event_type(channel)
    region_id = data.get("region_id") or _extract_region_from_channel(channel)

    return {
        "event_type": event_type,
        "region_id": region_id,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _map_channel_to_event_type(channel: str) -> str:
    """Map Redis channel pattern to SSE event type."""
    if "agent." in channel and ".alert" in channel:
        return "agent_assessment"
    if channel == ORCHESTRATOR_CASCADE_CHANNEL:
        return "cascade_update"
    if channel == ORCHESTRATOR_REROUTE_CHANNEL:
        return "route_recommended"
    return "disruption_detected"


def _extract_region_from_channel(channel: str) -> str | None:
    """Extract region_id from agent-specific channel patterns."""
    if not channel.startswith("agent."):
        return None
    parts = channel.split(".")
    if len(parts) >= 2:
        return parts[1]
    return None


def format_sse_event(
    event_type: str,
    data: dict[str, Any],
    region_id: str | None = None,
) -> str:
    """Format a structured SSE event payload."""
    payload = {
        "event_type": event_type,
        "region_id": region_id,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"


@router.get("/agents/stream")
async def stream_agent_events() -> StreamingResponse:
    """SSE endpoint for real-time agent status and disruption events."""
    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
