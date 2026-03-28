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
