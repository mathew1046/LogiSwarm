from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.schemas.orchestrator import (
    CascadeRiskRequest,
    EscalationRequest,
    OrchestratorEnvelope,
    SimulateRequest,
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


@router.post("/escalation", response_model=OrchestratorEnvelope)
async def evaluate_escalation(payload: EscalationRequest) -> OrchestratorEnvelope:
    decision = swarm_orchestrator.evaluate_escalation(
        region_id=payload.region_id,
        confidence=payload.confidence,
        payload=payload.model_dump(mode="json"),
    )
    return OrchestratorEnvelope(data=decision.model_dump(mode="json"), error=None, meta=None)


@router.post("/simulate", response_model=OrchestratorEnvelope)
async def simulate(payload: SimulateRequest) -> OrchestratorEnvelope:
    report = await swarm_orchestrator.run_simulation(
        scenario=payload.scenario,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    return OrchestratorEnvelope(data=report, error=None, meta=None)
