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

import asyncio
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from app.bus.connection import get_redis_client


class TMSWebhookPayload(BaseModel):
    """Normalized reroute payload sent to a downstream TMS webhook."""

    project_id: str = Field(min_length=1)
    shipment_ids: list[str] = Field(min_length=1)
    new_route: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    triggered_by: str = Field(min_length=1)


class TMSDispatchResult(BaseModel):
    """Dispatch outcome for TMS webhook delivery attempts."""

    model_config = ConfigDict(extra="allow")

    ok: bool
    attempts: int
    status_code: int | None = None
    response_body: str | None = None
    dead_lettered: bool = False
    dead_letter_reason: str | None = None
    dispatched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TMSWebhookClient:
    """Async TMS webhook client with HMAC signing and exponential backoff retries."""

    def __init__(
        self,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
        timeout_seconds: float = 8.0,
        max_retries: int = 3,
        dead_letter_key: str = "dead_letter:tms:webhook",
    ) -> None:
        self.webhook_url = (webhook_url or os.getenv("TMS_WEBHOOK_URL", "")).strip()
        self.webhook_secret = (webhook_secret or os.getenv("TMS_WEBHOOK_SECRET", "")).strip()
        self.timeout_seconds = float(os.getenv("TMS_WEBHOOK_TIMEOUT_SECONDS", str(timeout_seconds)))
        self.max_retries = int(os.getenv("TMS_WEBHOOK_MAX_RETRIES", str(max_retries)))
        self.dead_letter_key = os.getenv("TMS_WEBHOOK_DLQ_KEY", dead_letter_key)

    def _signature(self, raw_body: str) -> str:
        digest = hmac.new(
            key=self.webhook_secret.encode("utf-8"),
            msg=raw_body.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"

    async def dispatch(self, payload: TMSWebhookPayload) -> TMSDispatchResult:
        """Deliver reroute instruction to TMS endpoint with retries and DLQ fallback."""
        if not self.webhook_url:
            return await self._dead_letter(
                payload=payload,
                reason="TMS_WEBHOOK_URL is not configured",
                attempts=0,
            )

        if not self.webhook_secret:
            return await self._dead_letter(
                payload=payload,
                reason="TMS_WEBHOOK_SECRET is not configured",
                attempts=0,
            )

        raw_body = payload.model_dump_json()
        signature = self._signature(raw_body)
        headers = {
            "Content-Type": "application/json",
            "X-LogiSwarm-Signature": signature,
        }

        last_status: int | None = None
        last_response: str | None = None
        last_error: str | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        self.webhook_url,
                        content=raw_body,
                        headers=headers,
                    )
                last_status = response.status_code
                last_response = response.text

                if 200 <= response.status_code < 300:
                    return TMSDispatchResult(
                        ok=True,
                        attempts=attempt,
                        status_code=response.status_code,
                        response_body=response.text,
                        dead_lettered=False,
                    )

                if response.status_code not in {408, 425, 429, 500, 502, 503, 504}:
                    break
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = str(exc)

            if attempt < self.max_retries:
                await asyncio.sleep(2 ** (attempt - 1))

        reason = last_error or f"Webhook failed with status={last_status}, body={last_response}"
        dead_lettered = await self._dead_letter(payload=payload, reason=reason, attempts=self.max_retries)
        dead_lettered.status_code = last_status
        dead_lettered.response_body = last_response
        return dead_lettered

    async def _dead_letter(self, payload: TMSWebhookPayload, reason: str, attempts: int) -> TMSDispatchResult:
        record: dict[str, Any] = {
            "payload": payload.model_dump(mode="json"),
            "reason": reason,
            "attempts": attempts,
            "created_at": datetime.now(UTC).isoformat(),
        }

        try:
            redis = get_redis_client()
            await redis.rpush(self.dead_letter_key, json.dumps(record))
            await redis.expire(self.dead_letter_key, 7 * 24 * 3600)
            await redis.aclose()
        except Exception as exc:  # noqa: BLE001
            logger.bind(event="tms_dlq_write_failed", error=str(exc)).warning("Unable to write TMS event to DLQ")

        return TMSDispatchResult(
            ok=False,
            attempts=attempts,
            dead_lettered=True,
            dead_letter_reason=reason,
        )


tms_webhook_client = TMSWebhookClient()
