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
