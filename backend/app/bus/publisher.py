import json
from typing import Any

from app.bus.connection import get_redis_client


async def publish(channel: str, payload: dict[str, Any]) -> int:
    """Publish a JSON payload to a Redis pub/sub channel.

    Returns the number of subscribers the message was delivered to.
    """
    client = get_redis_client()
    try:
        message = json.dumps(payload, default=str)
        return await client.publish(channel, message)
    finally:
        await client.aclose()
