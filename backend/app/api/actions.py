from __future__ import annotations

from fastapi import APIRouter, Header
from loguru import logger

from app.actions.tms_webhook import TMSWebhookPayload, tms_webhook_client
from app.api.schemas.actions import ActionsEnvelope, TMSDispatchRequest, TMSDispatchResponse

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
