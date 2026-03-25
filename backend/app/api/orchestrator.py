from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.schemas.orchestrator import (
    CascadeRiskRequest,
    OrchestratorEnvelope,
)
from app.orchestrator.orchestrator import swarm_orchestrator

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/cascade-risk", response_model=OrchestratorEnvelope)
async def cascade_risk(payload: CascadeRiskRequest) -> OrchestratorEnvelope:
    result = swarm_orchestrator.cascade_risk(
        trigger_region=payload.trigger_region,
        severity=payload.severity,
    )
    return OrchestratorEnvelope(data=result.model_dump(mode="json"), error=None, meta=None)


@router.get("/risk-map", response_model=OrchestratorEnvelope)
async def risk_map() -> OrchestratorEnvelope:
    snapshot = swarm_orchestrator.get_global_risk_map()
    return OrchestratorEnvelope(data=snapshot, error=None, meta={"total": len(snapshot)})


@router.get("/risk-map/history", response_model=OrchestratorEnvelope)
async def risk_map_history(hours: int = Query(default=24, ge=1, le=168)) -> OrchestratorEnvelope:
    history = swarm_orchestrator.get_risk_map_history(hours=hours)
    return OrchestratorEnvelope(data=history, error=None, meta={"hours": hours, "total": len(history)})
