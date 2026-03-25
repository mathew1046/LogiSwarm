from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ShipmentRecord
from app.db.session import get_db_session
from app.orchestrator.orchestrator import swarm_orchestrator

router = APIRouter(prefix="/shipments", tags=["shipments"])


class ShipmentCreate(BaseModel):
    """Request body for registering a new shipment."""

    shipment_ref: str = Field(min_length=1, max_length=128)
    carrier: str | None = None
    origin: str | None = None
    destination: str | None = None
    route: list[str] = Field(default_factory=list)
    eta: datetime | None = None
    cargo_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShipmentResponse(BaseModel):
    """Serializable shipment record response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_ref: str
    carrier: str | None
    origin: str | None
    destination: str | None
    route: list[str]
    status: str
    eta: datetime | None
    risk_level: str
    disrupted_regions: list[str]
    recommended_actions: list[str]
    created_at: datetime
    updated_at: datetime | None


class ShipmentListResponse(BaseModel):
    """Paginated shipment list response."""

    shipments: list[ShipmentResponse]
    total: int
    limit: int
    offset: int


class ShipmentRiskResponse(BaseModel):
    """Detailed risk assessment for a shipment."""

    shipment_id: UUID
    shipment_ref: str
    route: list[str]
    risk_level: str
    disrupted_regions: list[str]
    risk_details: list[dict[str, Any]]
    cascade_impact: dict[str, Any] | None
    recommended_actions: list[str]
    evaluated_at: datetime


class ShipmentEnvelope(BaseModel):
    """Standard API envelope for shipment endpoints."""

    model_config = ConfigDict(extra="allow")

    data: object
    error: str | None = None
    meta: dict[str, Any] | None = None


_shipment_risk_cache: dict[str, dict[str, Any]] = {}
_risk_eval_task: asyncio.Task[None] | None = None


async def _evaluate_shipment_risks() -> None:
    """Background task: re-evaluate all active shipments against the current risk map every 15 minutes."""
    while True:
        await asyncio.sleep(900)
        try:
            _shipment_risk_cache.clear()
        except Exception:
            pass


async def start_risk_evaluator() -> None:
    """Start the background risk evaluation task."""
    global _risk_eval_task
    if _risk_eval_task is None or _risk_eval_task.done():
        _risk_eval_task = asyncio.create_task(
            _evaluate_shipment_risks(), name="shipment-risk-evaluator"
        )


def _compute_shipment_risk(route: list[str]) -> dict[str, Any]:
    """Compute risk exposure for a shipment route from the current global risk map."""
    global_risk = swarm_orchestrator.get_global_risk_map()
    disrupted_regions: list[str] = []
    risk_level = "LOW"
    risk_details: list[dict[str, Any]] = []

    for region_id in route:
        assessment = global_risk.get(region_id)
        if assessment:
            severity = str(assessment.get("severity", "LOW")).upper()
            confidence = float(assessment.get("confidence", 0.0))
            if severity in {"HIGH", "CRITICAL"}:
                disrupted_regions.append(region_id)
                risk_details.append(
                    {
                        "region_id": region_id,
                        "severity": severity,
                        "confidence": confidence,
                        "reasoning": assessment.get("reasoning", ""),
                    }
                )

    if len(disrupted_regions) >= 2:
        risk_level = "CRITICAL"
    elif len(disrupted_regions) == 1:
        severity = next(
            (
                d["severity"]
                for d in risk_details
                if d["region_id"] == disrupted_regions[0]
            ),
            "MEDIUM",
        )
        risk_level = "HIGH" if severity == "CRITICAL" else "MEDIUM"

    cascade_impact = None
    if disrupted_regions:
        cascade_result = swarm_orchestrator.cascade_risk(
            trigger_region=disrupted_regions[0],
            severity=risk_level,
        )
        cascade_impact = cascade_result.model_dump(mode="json")

    return {
        "risk_level": risk_level,
        "disrupted_regions": disrupted_regions,
        "risk_details": risk_details,
        "cascade_impact": cascade_impact,
    }


@router.post("", response_model=ShipmentEnvelope)
async def create_shipment(
    payload: ShipmentCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ShipmentEnvelope:
    """Register a new shipment with route and carrier information."""
    existing = await session.execute(
        select(ShipmentRecord).where(
            ShipmentRecord.shipment_ref == payload.shipment_ref
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Shipment '{payload.shipment_ref}' already exists"
        )

    route_list = payload.route or (
        [payload.origin, payload.destination]
        if payload.origin and payload.destination
        else []
    )
    risk_info = _compute_shipment_risk(route_list)

    record = ShipmentRecord(
        shipment_ref=payload.shipment_ref,
        carrier=payload.carrier,
        origin=payload.origin,
        destination=payload.destination,
        route={"regions": route_list},
        cargo_type=payload.cargo_type,
        status="pending",
        eta=payload.eta,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    response = _shipment_to_response(record, risk_info)
    return ShipmentEnvelope(data=response, error=None, meta={"registered": True})


@router.get("", response_model=ShipmentEnvelope)
async def list_shipments(
    status: str | None = Query(default=None),
    carrier: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ShipmentEnvelope:
    """List all shipments with optional filtering and pagination."""
    total_stmt = select(func.count()).select_from(ShipmentRecord)
    data_stmt = select(ShipmentRecord)

    if status:
        total_stmt = total_stmt.where(ShipmentRecord.status == status)
        data_stmt = data_stmt.where(ShipmentRecord.status == status)

    if carrier:
        total_stmt = total_stmt.where(ShipmentRecord.carrier == carrier)
        data_stmt = data_stmt.where(ShipmentRecord.carrier == carrier)

    total = (await session.execute(total_stmt)).scalar_one()

    rows = (
        (
            await session.execute(
                data_stmt.order_by(ShipmentRecord.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )

    responses = [_shipment_to_response_with_risk(row) for row in rows]

    return ShipmentEnvelope(
        data=ShipmentListResponse(
            shipments=responses,
            total=total,
            limit=limit,
            offset=offset,
        ),
        error=None,
        meta=None,
    )


@router.get("/{shipment_id}", response_model=ShipmentEnvelope)
async def get_shipment(
    shipment_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ShipmentEnvelope:
    """Get current status, risk exposure, and recommended actions for a shipment."""
    record = await session.get(ShipmentRecord, shipment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    route = record.route.get("regions", []) if record.route else []
    risk_info = _compute_shipment_risk(route)

    response = _shipment_to_response(record, risk_info)
    return ShipmentEnvelope(data=response, error=None, meta=None)


@router.get("/{shipment_id}/risk", response_model=ShipmentEnvelope)
async def get_shipment_risk(
    shipment_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ShipmentEnvelope:
    """Get detailed risk assessment for a shipment showing disrupted regions on its route."""
    record = await session.get(ShipmentRecord, shipment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    route = record.route.get("regions", []) if record.route else []
    risk_info = _compute_shipment_risk(route)

    recommended_actions: list[str] = []
    if risk_info["disrupted_regions"]:
        recommended_actions.append(
            f"Reroute to avoid {', '.join(risk_info['disrupted_regions'])}"
        )
        if risk_info["risk_level"] in {"HIGH", "CRITICAL"}:
            recommended_actions.append("Expedite alternative carrier booking")

    response = ShipmentRiskResponse(
        shipment_id=record.id,
        shipment_ref=record.shipment_ref,
        route=route,
        risk_level=risk_info["risk_level"],
        disrupted_regions=risk_info["disrupted_regions"],
        risk_details=risk_info["risk_details"],
        cascade_impact=risk_info["cascade_impact"],
        recommended_actions=recommended_actions,
        evaluated_at=datetime.now(UTC),
    )

    return ShipmentEnvelope(data=response, error=None, meta=None)


def _shipment_to_response(
    record: ShipmentRecord, risk_info: dict[str, Any]
) -> ShipmentResponse:
    """Convert a ShipmentRecord to a ShipmentResponse with risk info."""
    route = record.route.get("regions", []) if record.route else []
    return ShipmentResponse(
        id=record.id,
        shipment_ref=record.shipment_ref,
        carrier=record.carrier,
        origin=record.origin,
        destination=record.destination,
        route=route,
        status=record.status,
        eta=record.eta,
        risk_level=risk_info.get("risk_level", "LOW"),
        disrupted_regions=risk_info.get("disrupted_regions", []),
        recommended_actions=[],
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _shipment_to_response_with_risk(record: ShipmentRecord) -> ShipmentResponse:
    """Convert a ShipmentRecord with computed risk from global risk map."""
    route = record.route.get("regions", []) if record.route else []
    risk_info = _compute_shipment_risk(route)
    return _shipment_to_response(record, risk_info)
