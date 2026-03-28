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

import os
from typing import Optional

from redis.asyncio import ConnectionPool, Redis

_redis_pool: Optional[ConnectionPool] = None


def get_redis_url() -> str:
    """Resolve Redis connection URL from environment."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def init_redis_pool() -> ConnectionPool:
    """Initialize and return a global Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(get_redis_url(), decode_responses=True)
        client = Redis(connection_pool=_redis_pool)
        await client.ping()
        await client.aclose()
    return _redis_pool


def get_redis_client() -> Redis:
    """Return a Redis client bound to the initialized global connection pool."""
    if _redis_pool is None:
        raise RuntimeError("Redis pool is not initialized. Call init_redis_pool() first.")
    return Redis(connection_pool=_redis_pool)


async def close_redis_pool() -> None:
    """Close and reset the global Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
