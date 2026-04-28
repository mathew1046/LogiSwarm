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

import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm_core import ClaudeReasoningCore
from app.api.auth import require_operator, TokenPayload
from app.api.schemas.reroute import (
    RerouteEnvelope,
    RerouteExecuteRequest,
    RerouteExecuteResponse,
    RerouteRequest,
    RerouteResponse,
    RouteComparison,
)
from app.db.models import Route, ShipmentRecord
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reroute", tags=["reroute"])

REROUTE_SYSTEM_PROMPT = """You are a supply chain reroute decision-support analyst.
Given a current route and a proposed alternative route, analyze the tradeoffs and provide a recommendation.
Consider cost differences, transit time changes, reliability impacts, and any known disruptions.
Respond with a structured assessment covering risk level, reasoning for your recommendation, and confidence score."""


def _route_to_comparison(record: Route) -> RouteComparison:
    """Convert a Route model to RouteComparison for analysis response."""
    return RouteComparison(
        id=record.id,
        name=record.name,
        route_type=record.route_type,
        origin_region=record.origin_region,
        destination_region=record.destination_region,
        path=record.path or {},
        cost=record.cost,
        transit_hours=record.transit_hours,
        reliability=record.reliability,
        active=record.active,
        disrupted=record.disrupted,
    )


class LLMAssessment(BaseModel):
    """Structured LLM response for reroute analysis."""

    risk_assessment: str
    reasoning: str
    recommendation: str
    confidence: float


async def _call_llm_for_reroute(
    current_route: RouteComparison,
    proposed_route: RouteComparison,
    reason: str,
) -> LLMAssessment:
    """Call LLM to generate reroute analysis reasoning."""
    llm = ClaudeReasoningCore(agent_id="reroute_analyzer", mode="primary")

    user_prompt = f"""Analyze a reroute decision for a shipment.

Current Route:
- Name: {current_route.name}
- Type: {current_route.route_type}
- Origin: {current_route.origin_region}
- Destination: {current_route.destination_region}
- Cost: ${current_route.cost}k per TEU
- Transit Time: {current_route.transit_hours} hours
- Reliability: {current_route.reliability * 100}%

Proposed Route:
- Name: {proposed_route.name}
- Type: {proposed_route.route_type}
- Origin: {proposed_route.origin_region}
- Destination: {proposed_route.destination_region}
- Cost: ${proposed_route.cost}k per TEU
- Transit Time: {proposed_route.transit_hours} hours
- Reliability: {proposed_route.reliability * 100}%

Reason for reroute consideration: {reason}

Calculate the deltas:
- Cost change: ${proposed_route.cost - current_route.cost}k
- Transit time change: {proposed_route.transit_hours - current_route.transit_hours} hours
- Reliability change: {(proposed_route.reliability - current_route.reliability) * 100}%

Provide your analysis in JSON format:
{{
  "risk_assessment": "Brief assessment of risks (HIGH/MEDIUM/LOW)",
  "reasoning": "Detailed reasoning for your recommendation",
  "recommendation": "accept|reject|review",
  "confidence": 0.0-1.0
}}"""

    started_at = time.perf_counter()

    try:
        result = await llm.reason(
            payload={
                "system_prompt": REROUTE_SYSTEM_PROMPT,
                "events": [user_prompt],
                "memory_episodes": [],
            },
            use_fallback_on_error=True,
        )

        elapsed_ms = (time.perf_counter() - started_at) * 1000

        logger.info(
            {
                "event": "llm_reroute_analysis",
                "model": llm.model_name,
                "latency_ms": round(elapsed_ms, 2),
                "cost_estimate": round(
                    (elapsed_ms / 1000) * 0.001 * 15, 4
                ),  # rough estimate
            }
        )

        return LLMAssessment(
            risk_assessment=result.get("severity", "MEDIUM"),
            reasoning=result.get("reasoning", "Analysis completed"),
            recommendation=result.get("recommended_actions", ["review"])[0]
            if result.get("recommended_actions")
            else "review",
            confidence=result.get("confidence", 0.5),
        )

    except Exception as e:
        logger.warning({"event": "llm_call_failed", "error": str(e)})
        return LLMAssessment(
            risk_assessment="MEDIUM",
            reasoning=f"LLM analysis unavailable: {str(e)}",
            recommendation="review",
            confidence=0.3,
        )


@router.post("/analyze", response_model=RerouteEnvelope)
async def analyze_reroute(
    payload: RerouteRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RerouteEnvelope:
    """Analyze a proposed reroute by comparing current and proposed routes."""
    current_route = await session.get(Route, payload.current_route_id)
    if current_route is None:
        raise HTTPException(
            status_code=404, detail="Current route not found"
        )

    proposed_route = await session.get(Route, payload.proposed_route_id)
    if proposed_route is None:
        raise HTTPException(
            status_code=404, detail="Proposed route not found"
        )

    current_cmp = _route_to_comparison(current_route)
    proposed_cmp = _route_to_comparison(proposed_route)

    delta_cost = round(proposed_cmp.cost - current_cmp.cost, 2)
    delta_transit_hours = round(
        proposed_cmp.transit_hours - current_cmp.transit_hours, 2
    )
    delta_reliability = round(
        proposed_cmp.reliability - current_cmp.reliability, 4
    )

    llm_assessment = await _call_llm_for_reroute(
        current_cmp, proposed_cmp, payload.reason
    )

    analysis_id = uuid4()

    response_data = RerouteResponse(
        analysis_id=analysis_id,
        shipment_ref=payload.shipment_ref,
        current_route=current_cmp,
        proposed_route=proposed_cmp,
        delta_cost=delta_cost,
        delta_transit_hours=delta_transit_hours,
        delta_reliability=delta_reliability,
        risk_assessment=llm_assessment.risk_assessment,
        reasoning=llm_assessment.reasoning,
        recommendation=llm_assessment.recommendation,
        confidence=llm_assessment.confidence,
        cascade_impact=[],
    )

    return RerouteEnvelope(
        data=response_data.model_dump(mode="json"),
        error=None,
        meta={"analyzed_at": datetime.now(UTC).isoformat()},
    )


@router.post("/execute", response_model=RerouteEnvelope)
async def execute_reroute(
    payload: RerouteExecuteRequest,
    session: AsyncSession = Depends(get_db_session),
    _operator: TokenPayload = Depends(require_operator),
) -> RerouteEnvelope:
    """Execute a reroute decision, updating the shipment's route."""
    stmt = select(ShipmentRecord).where(
        ShipmentRecord.shipment_ref == payload.shipment_ref
    )
    result = await session.execute(stmt)
    shipment = result.scalar_one_or_none()

    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail=f"Shipment {payload.shipment_ref} not found",
        )

    previous_route_id = shipment.route.get("route_id") if shipment.route else None

    new_route = await session.get(Route, payload.new_route_id)
    if new_route is None:
        raise HTTPException(
            status_code=404, detail="New route not found"
        )

    shipment.route = {
        "route_id": str(new_route.id),
        "route_name": new_route.name,
        "route_type": new_route.route_type,
    }
    shipment.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(shipment)

    execution_id = uuid4()
    executed_at = datetime.now(UTC)

    logger.info(
        {
            "event": "reroute_executed",
            "execution_id": str(execution_id),
            "shipment_ref": payload.shipment_ref,
            "previous_route_id": str(previous_route_id) if previous_route_id else None,
            "new_route_id": str(payload.new_route_id),
            "approved_by": payload.approved_by,
            "operator": _operator.email,
        }
    )

    response_data = RerouteExecuteResponse(
        execution_id=execution_id,
        shipment_ref=payload.shipment_ref,
        previous_route_id=UUID(previous_route_id) if previous_route_id else UUID(int=0),
        new_route_id=payload.new_route_id,
        status="completed",
        executed_at=executed_at,
    )

    return RerouteEnvelope(
        data=response_data.model_dump(mode="json"),
        error=None,
        meta={"executed_by": _operator.email},
    )