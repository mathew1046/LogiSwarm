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

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import require_operator
from app.api.schemas.projects import Envelope, EnvelopeMeta
from app.orchestrator.scenario_builder import (
    Scenario,
    ScenarioBuilder,
    ScenarioComparison,
    ScenarioCreate,
    ScenarioMitigation,
    scenario_store,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
scenario_builder = ScenarioBuilder()


@router.post("", response_model=Envelope)
async def create_scenario(
    payload: ScenarioCreate,
    _operator: Any = Depends(require_operator),
) -> Envelope:
    """Create a new what-if disruption scenario and compute propagation impact."""
    scenario = scenario_builder.create_scenario(payload)
    return Envelope(
        data=scenario.model_dump(),
        error=None,
        meta={"scenario_id": scenario.scenario_id},
    )


@router.get("", response_model=Envelope)
async def list_scenarios(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Envelope:
    """List all saved scenarios."""
    scenarios = scenario_store.list(limit=limit, offset=offset)
    return Envelope(
        data=[s.model_dump() for s in scenarios],
        error=None,
        meta=EnvelopeMeta(total=len(scenarios), limit=limit, offset=offset),
    )


@router.get("/{scenario_id}", response_model=Envelope)
async def get_scenario(scenario_id: str) -> Envelope:
    """Get a specific scenario by ID."""
    scenario = scenario_store.get(scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found"
        )
    return Envelope(data=scenario.model_dump(), error=None, meta=None)


@router.post("/{scenario_id}/mitigation", response_model=Envelope)
async def add_mitigation(
    scenario_id: str,
    payload: ScenarioMitigation,
    _operator: Any = Depends(require_operator),
) -> Envelope:
    """Add a mitigation strategy to a scenario and compute mitigated impact."""
    scenario = scenario_builder.add_mitigation(scenario_id, payload)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found"
        )
    return Envelope(
        data=scenario.model_dump(),
        error=None,
        meta={"mitigation_added": True},
    )


@router.get("/{scenario_id}/compare", response_model=Envelope)
async def compare_scenario_impact(scenario_id: str) -> Envelope:
    """Compare current impact vs mitigated impact for a scenario."""
    comparison = scenario_builder.compare_impact(scenario_id)
    if comparison is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario_id}' not found or has no propagation result",
        )
    return Envelope(data=comparison.model_dump(), error=None, meta=None)


@router.delete("/{scenario_id}", response_model=Envelope)
async def delete_scenario(
    scenario_id: str,
    _operator: Any = Depends(require_operator),
) -> Envelope:
    """Delete a scenario."""
    deleted = scenario_store.delete(scenario_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found"
        )
    return Envelope(
        data={"deleted": True, "scenario_id": scenario_id}, error=None, meta=None
    )
