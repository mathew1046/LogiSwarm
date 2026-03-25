from __future__ import annotations

import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Header, Request
from loguru import logger

from app.actions.slack_notifier import slack_notifier
from app.actions.tms_webhook import TMSWebhookPayload, tms_webhook_client
from app.api.schemas.actions import (
    ActionsEnvelope,
    SlackAcceptResponse,
    SlackDispatchRequest,
    SlackDispatchResponse,
    TMSDispatchRequest,
    TMSDispatchResponse,
)

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
