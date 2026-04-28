from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.simple_runtime import PLACE_INDEX, PLACE_OPTIONS, simple_runtime


class Envelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: Any
    error: str | None = None
    meta: dict[str, Any] | None = None


class ShipmentRequest(BaseModel):
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)


router = APIRouter(tags=["simple-app"])


@router.get("/places", response_model=Envelope)
async def list_places() -> Envelope:
    return Envelope(data=PLACE_OPTIONS, error=None, meta={"total": len(PLACE_OPTIONS)})


@router.get("/dashboard", response_model=Envelope)
async def dashboard_state() -> Envelope:
    return Envelope(
        data={
            "shipment": simple_runtime.get_shipment(),
            "route_plan": simple_runtime.current_route_plan,
            "simulation": simple_runtime.get_simulation_status(),
            "places": PLACE_OPTIONS,
        },
        error=None,
        meta=None,
    )


@router.post("/shipments/current", response_model=Envelope)
async def set_current_shipment(payload: ShipmentRequest) -> Envelope:
    if payload.origin not in PLACE_INDEX or payload.destination not in PLACE_INDEX:
        raise HTTPException(status_code=400, detail="Origin or destination is invalid")
    if payload.origin == payload.destination:
        raise HTTPException(status_code=400, detail="Origin and destination must be different")

    shipment = simple_runtime.set_shipment(payload.origin, payload.destination)
    route_plan = simple_runtime.compute_routes(payload.origin, payload.destination)
    return Envelope(data={"shipment": shipment, "route_plan": route_plan}, error=None, meta=None)


@router.get("/shipments/current", response_model=Envelope)
async def get_current_shipment() -> Envelope:
    return Envelope(data=simple_runtime.get_shipment(), error=None, meta=None)


@router.get("/agents", response_model=Envelope)
async def list_agents() -> Envelope:
    agents = simple_runtime.get_agents()
    return Envelope(data=agents, error=None, meta={"total": len(agents)})


@router.get("/agents/topology", response_model=Envelope)
async def agent_topology() -> Envelope:
    return Envelope(data=simple_runtime.get_agent_topology(), error=None, meta=None)


@router.get("/routes/plan", response_model=Envelope)
async def get_route_plan() -> Envelope:
    if simple_runtime.current_route_plan is None:
        return Envelope(data=None, error=None, meta=None)
    return Envelope(data=simple_runtime.current_route_plan, error=None, meta=None)


@router.post("/routes/plan", response_model=Envelope)
async def compute_route_plan(payload: ShipmentRequest) -> Envelope:
    if payload.origin not in PLACE_INDEX or payload.destination not in PLACE_INDEX:
        raise HTTPException(status_code=400, detail="Origin or destination is invalid")
    recommendation = simple_runtime.compute_routes(payload.origin, payload.destination)
    return Envelope(data=recommendation, error=None, meta=None)


@router.post("/simulation/start", response_model=Envelope)
async def start_simulation() -> Envelope:
    try:
        simulation = simple_runtime.start_simulation()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Envelope(data=simulation, error=None, meta=None)


@router.get("/simulation/status", response_model=Envelope)
async def simulation_status() -> Envelope:
    return Envelope(data=simple_runtime.get_simulation_status(), error=None, meta=None)


@router.post("/simulation/stop", response_model=Envelope)
async def stop_simulation() -> Envelope:
    return Envelope(data=simple_runtime.stop_simulation(), error=None, meta=None)


@router.get("/reports", response_model=Envelope)
async def list_reports() -> Envelope:
    reports = simple_runtime.get_reports()
    return Envelope(data=reports, error=None, meta={"total": len(reports)})
