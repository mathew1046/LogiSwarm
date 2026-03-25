from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import parse_qs
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.audit_log import decision_audit_service
from app.actions.carrier_rebooking import carrier_rebooking_service
from app.actions.email_notifier import email_notifier
from app.actions.slack_notifier import slack_notifier
from app.actions.tms_webhook import TMSWebhookPayload, tms_webhook_client
from app.api.schemas.actions import (
    ActionsEnvelope,
    CarrierRebookingDispatchRequest,
    CarrierRebookingDispatchResponse,
    DecisionCreateRequest,
    DecisionCreateResponse,
    DecisionFeedbackRequest,
    DecisionFeedbackResponse,
    DecisionListMeta,
    DecisionListResponse,
    EmailDispatchRequest,
    EmailDispatchResponse,
    SlackAcceptResponse,
    SlackDispatchRequest,
    SlackDispatchResponse,
    TMSDispatchRequest,
    TMSDispatchResponse,
)
from app.db.session import get_db_session

router = APIRouter(tags=["actions"])


@router.post("/actions/tms/reroute", response_model=ActionsEnvelope)
async def dispatch_tms_reroute(payload: TMSDispatchRequest) -> ActionsEnvelope:
    """Dispatch signed reroute instruction to configured TMS webhook endpoint."""
    result = await tms_webhook_client.dispatch(payload.payload)
    return ActionsEnvelope(
        data=TMSDispatchResponse(result=result),
        error=None,
        meta={"dead_lettered": result.dead_lettered},
    )


@router.post("/actions/slack/alert", response_model=ActionsEnvelope)
async def dispatch_slack_alert(payload: SlackDispatchRequest) -> ActionsEnvelope:
    """Dispatch rich disruption alert to Slack webhook."""
    result = await slack_notifier.send_alert(payload.payload)
    return ActionsEnvelope(
        data=SlackDispatchResponse(result=result),
        error=None,
        meta={"delivered": result.ok},
    )


@router.post("/actions/email/alert", response_model=ActionsEnvelope)
async def dispatch_email_alert(payload: EmailDispatchRequest) -> ActionsEnvelope:
    """Dispatch disruption alert via HTML email with per-region throttling."""
    result = await email_notifier.send_alert(payload.payload)
    return ActionsEnvelope(
        data=EmailDispatchResponse(result=result),
        error=None,
        meta={"throttled": result.throttled},
    )


@router.post("/actions/carrier/rebook", response_model=ActionsEnvelope)
async def dispatch_carrier_rebooking(
    payload: CarrierRebookingDispatchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ActionsEnvelope:
    """Run carrier rebooking automation in recommend or auto-act mode."""
    result = await carrier_rebooking_service.process(payload.payload, session)
    return ActionsEnvelope(
        data=CarrierRebookingDispatchResponse(result=result),
        error=None,
        meta={"mode": result.mode, "shipments": len(result.results)},
    )


@router.post("/actions/slack/accept", response_model=ActionsEnvelope)
async def accept_slack_recommendation(request: Request) -> ActionsEnvelope:
    """Receive Slack action webhook payload for one-click recommendation acceptance."""
    raw_body = await request.body()
    decoded = raw_body.decode("utf-8") if raw_body else ""
    parsed = parse_qs(decoded)
    payload_raw = parsed.get("payload", ["{}"])[0]

    try:
        interaction_payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        interaction_payload = {}
    user_id = ((interaction_payload.get("user") or {}).get("id") or "")
    actions = interaction_payload.get("actions") or []
    first_action = actions[0] if actions else {}
    action_id = first_action.get("action_id")

    value_payload: dict[str, str] = {}
    action_value = first_action.get("value")
    if isinstance(action_value, str) and action_value:
        try:
            decoded_value = json.loads(action_value)
            if isinstance(decoded_value, dict):
                value_payload = {str(k): str(v) for k, v in decoded_value.items()}
        except json.JSONDecodeError:
            value_payload = {}

    response = SlackAcceptResponse(
        accepted=bool(action_id == "accept_recommendation"),
        action_id=action_id,
        user_id=user_id or None,
        project_id=value_payload.get("project_id"),
        region_id=value_payload.get("region_id"),
        recommendation=value_payload.get("top_recommendation"),
    )

    logger.bind(event="slack_accept_recommendation", payload=response.model_dump(mode="json")).info(
        "Received Slack accept recommendation action"
    )

    return ActionsEnvelope(data=response, error=None, meta=None)


@router.post("/mock/tms", response_model=ActionsEnvelope)
async def mock_tms_webhook(
    payload: TMSWebhookPayload,
    x_logiswarm_signature: str = Header(default="", alias="X-LogiSwarm-Signature"),
) -> ActionsEnvelope:
    """Development-only mock endpoint that logs incoming webhook payload and returns success."""
    logger.bind(
        event="mock_tms_webhook",
        signature=x_logiswarm_signature,
        payload=payload.model_dump(mode="json"),
    ).info("Mock TMS webhook received")

    return ActionsEnvelope(
        data={"accepted": True, "signature_received": bool(x_logiswarm_signature)},
        error=None,
        meta=None,
    )


@router.post("/decisions", response_model=ActionsEnvelope)
async def create_decision_log(
    payload: DecisionCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ActionsEnvelope:
    """Persist one decision audit log record."""
    row = await decision_audit_service.create_decision(payload.payload, session)
    return ActionsEnvelope(
        data=DecisionCreateResponse(decision=row),
        error=None,
        meta=None,
    )


@router.get("/decisions", response_model=ActionsEnvelope)
async def list_decision_logs(
    project_id: str | None = Query(default=None),
    region_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ActionsEnvelope:
    """List decision audit logs with optional project/region filtering and pagination."""
    rows, total = await decision_audit_service.list_decisions(
        session=session,
        project_id=project_id,
        region_id=region_id,
        limit=limit,
        offset=offset,
    )
    return ActionsEnvelope(
        data=DecisionListResponse(decisions=rows),
        error=None,
        meta=DecisionListMeta(
            total=total,
            limit=limit,
            offset=offset,
            project_id=project_id,
            region_id=region_id,
            generated_at=datetime.now(UTC),
        ).model_dump(mode="json"),
    )


@router.post("/decisions/{decision_id}/feedback", response_model=ActionsEnvelope)
async def submit_decision_feedback(
    decision_id: UUID,
    payload: DecisionFeedbackRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ActionsEnvelope:
    """Mark decision correctness and write feedback into memory."""
    result = await decision_audit_service.apply_feedback(
        decision_id=decision_id,
        payload=payload.payload,
        session=session,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    return ActionsEnvelope(
        data=DecisionFeedbackResponse(result=result),
        error=None,
        meta=None,
    )
