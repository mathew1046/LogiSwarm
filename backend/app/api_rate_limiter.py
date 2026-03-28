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

from __future__ import annotations

import os
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None
    RateLimitExceeded = Exception


DOCKER_NETWORK_IPS = [
    "172.16.0.0/12",
    "172.17.0.0/16",
    "172.18.0.0/15",
    "172.19.0.0/16",
    "10.0.0.0/8",
    "192.168.0.0/16",
]

LLM_ENDPOINT_LIMITS = {
    "/agents/{region_id}/interview": "10/minute",
    "/reports/generate": "10/minute",
    "/reports/{report_id}/chat": "10/minute",
}

GLOBAL_LIMIT = "1000/minute"


def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting.

    Prioritizes X-Forwarded-For header, then falls back to client IP.
    Internal Docker network IPs are whitelisted.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = get_remote_address(request)

    project_id = _extract_project_id(request)
    if project_id:
        return f"{client_ip}:{project_id}"

    return client_ip or "unknown"


def _extract_project_id(request: Request) -> str | None:
    """Extract project ID from request path or body."""
    path = request.url.path

    if "/projects/" in path:
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "projects" and i + 1 < len(parts):
                return parts[i + 1]

    return None


def _is_internal_ip(ip: str) -> bool:
    """Check if IP is from internal Docker network."""
    if not ip:
        return False

    if ip in ("127.0.0.1", "localhost", "::1"):
        return True

    if ip.startswith("172."):
        first_octet = int(ip.split(".")[1])
        if 16 <= first_octet <= 31:
            return True

    if ip.startswith("10."):
        return True

    if ip.startswith("192.168."):
        return True

    return False


def get_rate_limit_for_path(path: str) -> str:
    """Get the rate limit for a specific path."""
    for pattern, limit in LLM_ENDPOINT_LIMITS.items():
        pattern_base = pattern.split("/{")[0]
        if path.startswith(pattern_base):
            return limit

    return GLOBAL_LIMIT


def create_limiter():
    """Create and configure the rate limiter."""
    if not SLOWAPI_AVAILABLE:
        return None

    limiter = Limiter(
        key_func=get_client_identifier,
        default_limits=[GLOBAL_LIMIT],
        headers_enabled=True,
        storage_uri="memory://",
    )

    return limiter


limiter = create_limiter()


def rate_limit_exceeded_handler(request: Request, exc: Exception):
    """Handle rate limit exceeded errors with Retry-After header."""
    retry_after = "60"

    if hasattr(exc, "detail"):
        retry_after = str(exc.detail).split()[-1] if exc.detail else "60"

    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": retry_after,
        },
        headers={"Retry-After": retry_after},
    )

    return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests."""

    async def dispatch(self, request: Request, call_next):
        if _is_internal_ip(get_client_identifier(request).split(":")[0]):
            return await call_next(request)

        if limiter is None:
            return await call_next(request)

        path = request.url.path

        if path.startswith(("/health", "/metrics", "/docs", "/openapi.json", "/redoc")):
            return await call_next(request)

        try:
            return await call_next(request)
        except RateLimitExceeded as exc:
            return rate_limit_exceeded_handler(request, exc)


def get_limiter():
    """Get the configured limiter instance."""
    return limiter


if SLOWAPI_AVAILABLE:

    def rate_limit(limit: str = GLOBAL_LIMIT):
        """Decorator to apply rate limiting to specific endpoints."""
        if limiter is None:

            def decorator(func):
                return func

            return decorator
        return limiter.limit(limit)
else:

    def rate_limit(limit: str = GLOBAL_LIMIT):
        """No-op decorator when slowapi is not available."""

        def decorator(func):
            return func

        return decorator
