from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Route
from app.db.session import get_db_session

router = APIRouter(prefix="/routes", tags=["routes"])


class GeoJSONPath(BaseModel):
    """GeoJSON LineString representation of a route path."""

    type: str = "LineString"
    coordinates: list[list[float]] = Field(default_factory=list)


class RouteCreate(BaseModel):
    """Request body for creating a new route."""

    name: str = Field(min_length=1, max_length=255)
    route_type: str = Field(min_length=1, max_length=32)
    origin_region: str = Field(min_length=1, max_length=128)
    destination_region: str = Field(min_length=1, max_length=128)
    path: GeoJSONPath = Field(default_factory=GeoJSONPath)
    cost: float = Field(default=0.0, ge=0)
    transit_hours: float = Field(default=0.0, ge=0)
    reliability: float = Field(default=0.9, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteResponse(BaseModel):
    """Serializable route record response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    route_type: str
    origin_region: str
    destination_region: str
    path: dict[str, Any]
    cost: float
    transit_hours: float
    reliability: float
    active: bool
    disrupted: bool
    disruption_reason: str | None
    created_at: datetime
    updated_at: datetime | None


class RouteListResponse(BaseModel):
    """Paginated route list response."""

    routes: list[RouteResponse]
    total: int
    limit: int
    offset: int


class RouteDisablePayload(BaseModel):
    """Request body for marking a route as disrupted."""

    reason: str | None = Field(default=None, max_length=500)


class RouteEnvelope(BaseModel):
    """Standard API envelope for route endpoints."""

    model_config = ConfigDict(extra="allow")

    data: object
    error: str | None = None
    meta: dict[str, Any] | None = None


ROUTE_TYPE_SEED_DATA: list[dict[str, Any]] = [
    {
        "name": "Shanghai - Singapore Sea Lane",
        "route_type": "sea",
        "origin_region": "china_ea",
        "destination_region": "se_asia",
        "cost": 1.2,
        "transit_hours": 96.0,
        "reliability": 0.92,
        "path": {
            "type": "LineString",
            "coordinates": [[121.47, 31.23], [103.83, 1.35]],
        },
    },
    {
        "name": "Singapore - Suez Sea Lane",
        "route_type": "sea",
        "origin_region": "se_asia",
        "destination_region": "gulf_suez",
        "cost": 1.3,
        "transit_hours": 168.0,
        "reliability": 0.88,
        "path": {"type": "LineString", "coordinates": [[103.83, 1.35], [32.35, 29.95]]},
    },
    {
        "name": "Suez - Rotterdam Sea Lane",
        "route_type": "sea",
        "origin_region": "gulf_suez",
        "destination_region": "europe",
        "cost": 1.1,
        "transit_hours": 120.0,
        "reliability": 0.91,
        "path": {"type": "LineString", "coordinates": [[32.35, 29.95], [4.29, 51.92]]},
    },
    {
        "name": "Rotterdam - New York Sea Lane",
        "route_type": "sea",
        "origin_region": "europe",
        "destination_region": "north_america",
        "cost": 1.5,
        "transit_hours": 144.0,
        "reliability": 0.89,
        "path": {"type": "LineString", "coordinates": [[4.29, 51.92], [-74.0, 40.71]]},
    },
    {
        "name": "Shanghai - LA Sea Lane (Pacific)",
        "route_type": "sea",
        "origin_region": "china_ea",
        "destination_region": "north_america",
        "cost": 2.1,
        "transit_hours": 336.0,
        "reliability": 0.85,
        "path": {
            "type": "LineString",
            "coordinates": [[121.47, 31.23], [-118.24, 33.97]],
        },
    },
    {
        "name": "Shanghai - Hong Kong Sea Lane",
        "route_type": "sea",
        "origin_region": "china_ea",
        "destination_region": "china_ea",
        "cost": 0.5,
        "transit_hours": 48.0,
        "reliability": 0.95,
        "path": {
            "type": "LineString",
            "coordinates": [[121.47, 31.23], [114.17, 22.28]],
        },
    },
    {
        "name": "Hong Kong - Singapore Sea Lane",
        "route_type": "sea",
        "origin_region": "china_ea",
        "destination_region": "se_asia",
        "cost": 0.8,
        "transit_hours": 72.0,
        "reliability": 0.93,
        "path": {
            "type": "LineString",
            "coordinates": [[114.17, 22.28], [103.83, 1.35]],
        },
    },
    {
        "name": "Singapore - Mumbai Sea Lane",
        "route_type": "sea",
        "origin_region": "se_asia",
        "destination_region": "south_asia",
        "cost": 1.0,
        "transit_hours": 96.0,
        "reliability": 0.90,
        "path": {"type": "LineString", "coordinates": [[103.83, 1.35], [72.88, 18.98]]},
    },
    {
        "name": "Suez - Dubai Sea Lane",
        "route_type": "sea",
        "origin_region": "gulf_suez",
        "destination_region": "gulf_suez",
        "cost": 0.6,
        "transit_hours": 48.0,
        "reliability": 0.87,
        "path": {"type": "LineString", "coordinates": [[32.35, 29.95], [55.27, 25.20]]},
    },
    {
        "name": "Rotterdam - Hamburg Rail Corridor",
        "route_type": "rail",
        "origin_region": "europe",
        "destination_region": "europe",
        "cost": 0.3,
        "transit_hours": 12.0,
        "reliability": 0.95,
        "path": {"type": "LineString", "coordinates": [[4.29, 51.92], [9.99, 53.55]]},
    },
    {
        "name": "LA - Chicago Rail Corridor",
        "route_type": "rail",
        "origin_region": "north_america",
        "destination_region": "north_america",
        "cost": 0.8,
        "transit_hours": 72.0,
        "reliability": 0.92,
        "path": {
            "type": "LineString",
            "coordinates": [[-118.24, 33.97], [-87.63, 41.88]],
        },
    },
    {
        "name": "Shanghai - LA Air Freight",
        "route_type": "air",
        "origin_region": "china_ea",
        "destination_region": "north_america",
        "cost": 12.0,
        "transit_hours": 24.0,
        "reliability": 0.97,
        "path": {
            "type": "LineString",
            "coordinates": [[121.47, 31.23], [-118.24, 33.97]],
        },
    },
    {
        "name": "Hong Kong - Frankfurt Air Freight",
        "route_type": "air",
        "origin_region": "china_ea",
        "destination_region": "europe",
        "cost": 14.0,
        "transit_hours": 20.0,
        "reliability": 0.96,
        "path": {"type": "LineString", "coordinates": [[114.17, 22.28], [8.68, 50.11]]},
    },
    {
        "name": "Singapore - Sydney Sea Lane",
        "route_type": "sea",
        "origin_region": "se_asia",
        "destination_region": "oceania",
        "cost": 1.8,
        "transit_hours": 192.0,
        "reliability": 0.91,
        "path": {
            "type": "LineString",
            "coordinates": [[103.83, 1.35], [151.21, -33.87]],
        },
    },
    {
        "name": "Rotterdam - Antwerp Sea Lane",
        "route_type": "sea",
        "origin_region": "europe",
        "destination_region": "europe",
        "cost": 0.2,
        "transit_hours": 6.0,
        "reliability": 0.98,
        "path": {"type": "LineString", "coordinates": [[4.29, 51.92], [4.40, 51.22]]},
    },
    {
        "name": "Panama - Los Angeles Sea Lane",
        "route_type": "sea",
        "origin_region": "latin_america",
        "destination_region": "north_america",
        "cost": 1.4,
        "transit_hours": 120.0,
        "reliability": 0.88,
        "path": {
            "type": "LineString",
            "coordinates": [[-79.52, 8.98], [-118.24, 33.97]],
        },
    },
    {
        "name": "Santos - Rotterdam Sea Lane",
        "route_type": "sea",
        "origin_region": "latin_america",
        "destination_region": "europe",
        "cost": 2.2,
        "transit_hours": 240.0,
        "reliability": 0.86,
        "path": {
            "type": "LineString",
            "coordinates": [[-46.33, -23.55], [4.29, 51.92]],
        },
    },
    {
        "name": "Cape Town - Rotterdam Sea Lane",
        "route_type": "sea",
        "origin_region": "africa",
        "destination_region": "europe",
        "cost": 2.0,
        "transit_hours": 216.0,
        "reliability": 0.89,
        "path": {"type": "LineString", "coordinates": [[18.42, -33.93], [4.29, 51.92]]},
    },
    {
        "name": "Dubai - Mumbai Sea Lane",
        "route_type": "sea",
        "origin_region": "gulf_suez",
        "destination_region": "south_asia",
        "cost": 0.7,
        "transit_hours": 60.0,
        "reliability": 0.90,
        "path": {"type": "LineString", "coordinates": [[55.27, 25.20], [72.88, 18.98]]},
    },
    {
        "name": "Mumbai - Singapore Sea Lane",
        "route_type": "sea",
        "origin_region": "south_asia",
        "destination_region": "se_asia",
        "cost": 1.0,
        "transit_hours": 96.0,
        "reliability": 0.90,
        "path": {"type": "LineString", "coordinates": [[72.88, 18.98], [103.83, 1.35]]},
    },
]


async def seed_routes_if_empty(session: AsyncSession) -> None:
    """Seed initial route data if the routes table is empty."""
    count_stmt = select(func.count()).select_from(Route)
    existing_count = (await session.execute(count_stmt)).scalar_one()
    if existing_count > 0:
        return

    for seed in ROUTE_TYPE_SEED_DATA:
        route = Route(
            name=seed["name"],
            route_type=seed["route_type"],
            origin_region=seed["origin_region"],
            destination_region=seed["destination_region"],
            path=seed.get("path", {}),
            cost=float(seed.get("cost", 0.0)),
            transit_hours=float(seed.get("transit_hours", 0.0)),
            reliability=float(seed.get("reliability", 0.9)),
            active=True,
            disrupted=False,
        )
        session.add(route)

    await session.commit()


@router.get("", response_model=RouteEnvelope)
async def list_routes(
    route_type: str | None = Query(default=None),
    origin_region: str | None = Query(default=None),
    destination_region: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> RouteEnvelope:
    """List all known routes with optional filtering."""
    total_stmt = select(func.count()).select_from(Route)
    data_stmt = select(Route)

    if route_type:
        total_stmt = total_stmt.where(Route.route_type == route_type)
        data_stmt = data_stmt.where(Route.route_type == route_type)

    if origin_region:
        total_stmt = total_stmt.where(Route.origin_region == origin_region)
        data_stmt = data_stmt.where(Route.origin_region == origin_region)

    if destination_region:
        total_stmt = total_stmt.where(Route.destination_region == destination_region)
        data_stmt = data_stmt.where(Route.destination_region == destination_region)

    if active_only:
        total_stmt = total_stmt.where(Route.active == True)
        data_stmt = data_stmt.where(Route.active == True)

    total = (await session.execute(total_stmt)).scalar_one()

    rows = (
        (
            await session.execute(
                data_stmt.order_by(Route.created_at.desc()).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )

    responses = [_route_to_response(row) for row in rows]

    return RouteEnvelope(
        data=RouteListResponse(
            routes=responses,
            total=total,
            limit=limit,
            offset=offset,
        ),
        error=None,
        meta=None,
    )


@router.post("", response_model=RouteEnvelope)
async def create_route(
    payload: RouteCreate,
    session: AsyncSession = Depends(get_db_session),
) -> RouteEnvelope:
    """Add a new route (sea lane, air, or rail) with GeoJSON path."""
    record = Route(
        name=payload.name,
        route_type=payload.route_type,
        origin_region=payload.origin_region,
        destination_region=payload.destination_region,
        path=payload.path.model_dump(mode="json"),
        cost=payload.cost,
        transit_hours=payload.transit_hours,
        reliability=payload.reliability,
        active=True,
        disrupted=False,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return RouteEnvelope(
        data=_route_to_response(record), error=None, meta={"created": True}
    )


@router.get("/{route_id}", response_model=RouteEnvelope)
async def get_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> RouteEnvelope:
    """Get a specific route by ID."""
    record = await session.get(Route, route_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Route not found")

    return RouteEnvelope(data=_route_to_response(record), error=None, meta=None)


@router.put("/{route_id}/disable", response_model=RouteEnvelope)
async def disable_route(
    route_id: UUID,
    payload: RouteDisablePayload,
    session: AsyncSession = Depends(get_db_session),
) -> RouteEnvelope:
    """Mark a route as disrupted (manual override)."""
    record = await session.get(Route, route_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Route not found")

    record.disrupted = True
    record.disruption_reason = payload.reason
    record.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(record)

    return RouteEnvelope(
        data=_route_to_response(record), error=None, meta={"disabled": True}
    )


@router.put("/{route_id}/enable", response_model=RouteEnvelope)
async def enable_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> RouteEnvelope:
    """Re-enable a previously disrupted route."""
    record = await session.get(Route, route_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Route not found")

    record.disrupted = False
    record.disruption_reason = None
    record.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(record)

    return RouteEnvelope(
        data=_route_to_response(record), error=None, meta={"enabled": True}
    )


def _route_to_response(record: Route) -> RouteResponse:
    """Convert a Route model to RouteResponse."""
    return RouteResponse(
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
        disruption_reason=record.disruption_reason,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
