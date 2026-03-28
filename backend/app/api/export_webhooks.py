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

import csv
import io
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.projects import Envelope, EnvelopeMeta
from app.db.base import SessionLocal


ExportFormat = Literal["csv", "json"]


class WebhookRegistration(BaseModel):
    """Request body for registering a new webhook."""

    url: str = Field(min_length=10, max_length=2048)
    name: str = Field(min_length=3, max_length=128)
    secret: str | None = Field(default=None, max_length=256)
    event_types: list[str] = Field(default_factory=lambda: ["disruption"])
    active: bool = Field(default=True)


class WebhookResponse(BaseModel):
    """Response for webhook registration."""

    model_config = ConfigDict(extra="allow")

    webhook_id: str
    url: str
    name: str
    event_types: list[str]
    active: bool
    created_at: str


class WebhookDelivery(BaseModel):
    """Webhook delivery attempt record."""

    model_config = ConfigDict(extra="allow")

    webhook_id: str
    event_type: str
    payload: dict[str, Any]
    status: str
    attempts: int
    last_attempt_at: str
    error: str | None = None


_webhooks_store: dict[str, dict[str, Any]] = {}
_webhook_deliveries: list[dict[str, Any]] = []

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookResponse)
async def register_webhook(payload: WebhookRegistration) -> WebhookResponse:
    """Register a new webhook endpoint to receive disruption events."""
    webhook_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    _webhooks_store[webhook_id] = {
        "webhook_id": webhook_id,
        "url": payload.url,
        "name": payload.name,
        "secret": payload.secret,
        "event_types": payload.event_types,
        "active": payload.active,
        "created_at": now,
        "failure_count": 0,
    }

    return WebhookResponse(
        webhook_id=webhook_id,
        url=payload.url,
        name=payload.name,
        event_types=payload.event_types,
        active=payload.active,
        created_at=now,
    )


@router.get("", response_model=Envelope)
async def list_webhooks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Envelope:
    """List all registered webhooks."""
    webhooks = [
        {k: v for k, v in wh.items() if k != "secret"}
        for wh in _webhooks_store.values()
    ]
    webhooks = sorted(webhooks, key=lambda x: x["created_at"], reverse=True)
    return Envelope(
        data=webhooks[offset : offset + limit],
        error=None,
        meta=EnvelopeMeta(total=len(webhooks), limit=limit, offset=offset),
    )


@router.get("/{webhook_id}", response_model=Envelope)
async def get_webhook(webhook_id: str) -> Envelope:
    """Get a specific webhook by ID."""
    webhook = _webhooks_store.get(webhook_id)
    if webhook is None:
        raise HTTPException(status_code=404, detail=f"Webhook '{webhook_id}' not found")
    data = {k: v for k, v in webhook.items() if k != "secret"}
    return Envelope(data=data, error=None, meta=None)


@router.delete("/{webhook_id}", response_model=Envelope)
async def delete_webhook(webhook_id: str) -> Envelope:
    """Delete a webhook registration."""
    if webhook_id not in _webhooks_store:
        raise HTTPException(status_code=404, detail=f"Webhook '{webhook_id}' not found")
    del _webhooks_store[webhook_id]
    return Envelope(
        data={"deleted": True, "webhook_id": webhook_id}, error=None, meta=None
    )


@router.put("/{webhook_id}/toggle", response_model=WebhookResponse)
async def toggle_webhook(
    webhook_id: str, active: bool = Query(default=True)
) -> WebhookResponse:
    """Toggle webhook active status."""
    webhook = _webhooks_store.get(webhook_id)
    if webhook is None:
        raise HTTPException(status_code=404, detail=f"Webhook '{webhook_id}' not found")
    webhook["active"] = active
    return WebhookResponse(
        webhook_id=webhook_id,
        url=webhook["url"],
        name=webhook["name"],
        event_types=webhook["event_types"],
        active=webhook["active"],
        created_at=webhook["created_at"],
    )


@router.get("/{webhook_id}/deliveries", response_model=Envelope)
async def list_webhook_deliveries(
    webhook_id: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> Envelope:
    """List delivery attempts for a webhook."""
    deliveries = [d for d in _webhook_deliveries if d["webhook_id"] == webhook_id]
    deliveries = sorted(deliveries, key=lambda x: x["last_attempt_at"], reverse=True)
    return Envelope(
        data=deliveries[:limit],
        error=None,
        meta={"webhook_id": webhook_id, "total": len(deliveries)},
    )


def build_disruption_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Build a webhook payload matching Slack alert format."""
    return {
        "event_type": "disruption",
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {
            "disruption_id": event.get("id"),
            "region_id": event.get("region_id"),
            "severity": event.get("severity"),
            "signal_type": event.get("signal_type"),
            "detected_at": event.get("detected_at"),
            "cascade_score": event.get("cascade_score"),
            "affected_routes": event.get("affected_routes", []),
            "recommendation": event.get("recommendation"),
            "confidence": event.get("confidence"),
        },
    }


export_router = APIRouter(prefix="/export", tags=["export"])


@router.get("/disruptions", response_model=Envelope)
async def export_disruptions(
    start_date: str = Query(default=None, description="Start date (ISO format)"),
    end_date: str = Query(default=None, description="End date (ISO format)"),
    region_id: str | None = Query(default=None, description="Filter by region ID"),
    format: ExportFormat = Query(
        default="json", description="Export format: csv or json"
    ),
    limit: int = Query(default=1000, ge=1, le=10000),
) -> Envelope:
    """Export disruption events in CSV or JSON format."""
    from app.db.models import DisruptionEvent

    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid start_date format: {start_date}"
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid end_date format: {end_date}"
            )

    with SessionLocal() as session:
        query = select(DisruptionEvent).order_by(DisruptionEvent.detected_at.desc())

        if start_dt:
            query = query.where(DisruptionEvent.detected_at >= start_dt)
        if end_dt:
            query = query.where(DisruptionEvent.detected_at <= end_dt)
        if region_id:
            try:
                region_uuid = uuid.UUID(region_id)
                query = query.where(DisruptionEvent.region_id == region_uuid)
            except ValueError:
                pass

        query = query.limit(limit)
        result = session.execute(query)
        events = result.scalars().all()

    records = [
        {
            "id": str(event.id),
            "region_id": str(event.region_id),
            "severity": event.severity,
            "signal_type": event.signal_type,
            "detected_at": event.detected_at.isoformat() if event.detected_at else None,
            "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
            "cascade_score": event.cascade_score,
        }
        for event in events
    ]

    if format == "csv":
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        csv_data = output.getvalue()
        return Envelope(
            data={"format": "csv", "records": len(records), "csv_content": csv_data},
            error=None,
            meta=EnvelopeMeta(total=len(records), limit=limit, offset=0),
        )

    return Envelope(
        data=records,
        error=None,
        meta=EnvelopeMeta(total=len(records), limit=limit, offset=0),
    )
