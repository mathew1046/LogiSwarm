from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.actions.audit_log import (
    DecisionFeedbackPayload,
    DecisionFeedbackResult,
    DecisionLogCreatePayload,
    DecisionLogResponse,
)
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


class DecisionCreateRequest(BaseModel):
    """Request body for persisting a decision audit record."""

    payload: DecisionLogCreatePayload


class DecisionCreateResponse(BaseModel):
    """Typed response payload for one created decision record."""

    decision: DecisionLogResponse


class DecisionFeedbackRequest(BaseModel):
    """Request body for marking a decision outcome and feedback details."""

    payload: DecisionFeedbackPayload


class DecisionFeedbackResponse(BaseModel):
    """Typed response payload for decision feedback update."""

    result: DecisionFeedbackResult


class DecisionListResponse(BaseModel):
    """Typed list response payload for decision log queries."""

    decisions: list[DecisionLogResponse]


class DecisionListMeta(BaseModel):
    """Pagination metadata returned by decision log list endpoint."""

    total: int
    limit: int
    offset: int
    project_id: str | None = None
    region_id: str | None = None
    generated_at: datetime
