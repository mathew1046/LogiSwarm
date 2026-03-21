import asyncio
import json
from typing import Any, Awaitable, Callable

from app.bus.connection import get_redis_client

MessageHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


async def subscribe(channel: str, handler: MessageHandler) -> None:
    """Subscribe to a Redis channel and invoke `handler` for each message."""
    client = get_redis_client()
    pubsub = client.pubsub()

    try:
        await pubsub.subscribe(channel)
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message and message.get("type") == "message":
                data = message.get("data")
                if isinstance(data, str):
                    payload = json.loads(data)
                elif isinstance(data, bytes):
                    payload = json.loads(data.decode("utf-8"))
                else:
                    payload = data

                result = handler(payload)
                if asyncio.iscoroutine(result):
                    await result

            await asyncio.sleep(0.05)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await client.aclose()
