from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.actions.tms_webhook import TMSDispatchResult, TMSWebhookPayload


class ActionsEnvelope(BaseModel):
    """Standard response envelope for action-layer endpoints."""

    model_config = ConfigDict(extra="allow")

    data: object
    error: str | None = None
    meta: dict | None = None


class TMSDispatchRequest(BaseModel):
    """Request body for direct TMS reroute dispatch endpoint."""

    payload: TMSWebhookPayload


class TMSDispatchResponse(BaseModel):
    """Typed response payload for TMS dispatch results."""

    result: TMSDispatchResult
