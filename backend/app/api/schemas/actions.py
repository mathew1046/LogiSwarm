from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.actions.carrier_rebooking import CarrierRebookingRequest, CarrierRebookingResponse
from app.actions.email_notifier import EmailAlertPayload, EmailNotifyResult
from app.actions.slack_notifier import SlackAlertPayload, SlackNotifyResult
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


class SlackDispatchRequest(BaseModel):
    """Request body for dispatching disruption alerts to Slack."""

    payload: SlackAlertPayload


class SlackDispatchResponse(BaseModel):
    """Typed response payload for Slack alert delivery results."""

    result: SlackNotifyResult


class SlackAcceptResponse(BaseModel):
    """Typed webhook action payload for accepted Slack recommendations."""

    accepted: bool
    action_id: str | None = None
    user_id: str | None = None
    project_id: str | None = None
    region_id: str | None = None
    recommendation: str | None = None


class EmailDispatchRequest(BaseModel):
    """Request body for dispatching disruption alerts via email."""

    payload: EmailAlertPayload


class EmailDispatchResponse(BaseModel):
    """Typed response payload for email alert delivery results."""

    result: EmailNotifyResult


class CarrierRebookingDispatchRequest(BaseModel):
    """Request body for carrier rebooking automation."""

    payload: CarrierRebookingRequest


class CarrierRebookingDispatchResponse(BaseModel):
    """Typed response payload for carrier rebooking results."""

    result: CarrierRebookingResponse
