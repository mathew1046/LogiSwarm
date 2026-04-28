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

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.auth import require_operator
from app.api.schemas.orchestrator import (
    CascadeRiskRequest,
    EscalationRequest,
    OrchestratorEnvelope,
    SimulateRequest,
)
from app.orchestrator.orchestrator import swarm_orchestrator

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/cascade-risk", response_model=OrchestratorEnvelope)
async def cascade_risk(
    payload: CascadeRiskRequest,
    _operator: Any = Depends(require_operator),
) -> OrchestratorEnvelope:
    """Compute cascade risk propagation from a trigger region."""
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
async def evaluate_escalation(
    payload: EscalationRequest,
    _operator: Any = Depends(require_operator),
) -> OrchestratorEnvelope:
    """Evaluate escalation decision based on confidence and region thresholds."""
    decision = swarm_orchestrator.evaluate_escalation(
        region_id=payload.region_id,
        confidence=payload.confidence,
        payload=payload.model_dump(mode="json"),
    )
    return OrchestratorEnvelope(data=decision.model_dump(mode="json"), error=None, meta=None)


@router.post("/simulate", response_model=OrchestratorEnvelope)
async def simulate(
    payload: SimulateRequest,
    _operator: Any = Depends(require_operator),
) -> OrchestratorEnvelope:
    """Run a historical disruption simulation scenario."""
    from datetime import UTC, datetime

    start_date = payload.start_date or datetime(2020, 1, 1, tzinfo=UTC)
    end_date = payload.end_date or datetime.now(UTC)

    report = await swarm_orchestrator.run_simulation(
        scenario=payload.scenario,
        start_date=start_date,
        end_date=end_date,
        scenario_id=payload.scenario_id,
    )
    return OrchestratorEnvelope(data=report, error=None, meta=None)
