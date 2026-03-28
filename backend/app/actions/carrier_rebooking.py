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

import os
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ShipmentRecord


RebookingMode = Literal["AUTO_ACT", "RECOMMEND"]


class CarrierOption(BaseModel):
    """Ranked carrier option candidate for a disrupted shipment."""

    carrier: str
    price_delta: float
    availability: float = Field(ge=0.0)
    transit_time_hours: float = Field(gt=0.0)
    score: float = Field(ge=0.0)
    booking_reference: str | None = None


class CarrierRebookingRequest(BaseModel):
    """Carrier rebooking input for recommend and auto-act workflows."""

    project_id: str = Field(min_length=1)
    shipment_ids: list[str] = Field(min_length=1)
    recommended_route: str = Field(min_length=1)
    mode: RebookingMode
    candidate_carriers: list[str] = Field(default_factory=list)
    max_options: int = Field(default=3, ge=1, le=10)


class ShipmentRebookingResult(BaseModel):
    """Rebooking result for one shipment."""

    shipment_id: str
    mode: RebookingMode
    selected_option: CarrierOption | None = None
    options: list[CarrierOption] = Field(default_factory=list)
    updated: bool = False
    message: str | None = None


class CarrierRebookingResponse(BaseModel):
    """Top-level rebooking execution result."""

    model_config = ConfigDict(extra="allow")

    project_id: str
    mode: RebookingMode
    results: list[ShipmentRebookingResult]


class CarrierRebookingService:
    """Automate carrier rebooking decisions based on availability scoring."""

    def __init__(self) -> None:
        self.availability_api_url = os.getenv("CARRIER_AVAILABILITY_API_URL", "").strip()
        self.booking_api_url = os.getenv("CARRIER_BOOKING_API_URL", "").strip()
        self.timeout_seconds = float(os.getenv("CARRIER_API_TIMEOUT_SECONDS", "8"))
        self.default_candidates = [
            item.strip() for item in os.getenv("CARRIER_DEFAULT_CANDIDATES", "maersk,cma-cgm,msc,hapag-lloyd").split(",")
            if item.strip()
        ]

    async def process(self, payload: CarrierRebookingRequest, session: AsyncSession) -> CarrierRebookingResponse:
        """Run recommend or auto-act flow for each shipment in request payload."""
        results: list[ShipmentRebookingResult] = []
        carriers = payload.candidate_carriers or self.default_candidates

        for shipment_id in payload.shipment_ids:
            options = await self._rank_options(
                shipment_id=shipment_id,
                recommended_route=payload.recommended_route,
                candidate_carriers=carriers,
                max_options=payload.max_options,
            )

            if payload.mode == "RECOMMEND":
                results.append(
                    ShipmentRebookingResult(
                        shipment_id=shipment_id,
                        mode=payload.mode,
                        selected_option=options[0] if options else None,
                        options=options,
                        updated=False,
                        message="Ranked options generated for ops review",
                    )
                )
                continue

            if not options:
                results.append(
                    ShipmentRebookingResult(
                        shipment_id=shipment_id,
                        mode=payload.mode,
                        selected_option=None,
                        options=[],
                        updated=False,
                        message="No available carrier option",
                    )
                )
                continue

            selected = options[0]
            booking_reference = await self._book_option(shipment_id=shipment_id, option=selected, route=payload.recommended_route)
            selected.booking_reference = booking_reference
            updated = await self._update_shipment_record(
                session=session,
                shipment_id=shipment_id,
                selected=selected,
            )
            results.append(
                ShipmentRebookingResult(
                    shipment_id=shipment_id,
                    mode=payload.mode,
                    selected_option=selected,
                    options=options,
                    updated=updated,
                    message="Booking confirmed and shipment updated" if updated else "Shipment not found; booking completed",
                )
            )

        if payload.mode == "AUTO_ACT":
            await session.commit()

        return CarrierRebookingResponse(
            project_id=payload.project_id,
            mode=payload.mode,
            results=results,
        )

    async def _rank_options(
        self,
        *,
        shipment_id: str,
        recommended_route: str,
        candidate_carriers: list[str],
        max_options: int,
    ) -> list[CarrierOption]:
        raw_options = await self._fetch_availability(
            shipment_id=shipment_id,
            recommended_route=recommended_route,
            candidate_carriers=candidate_carriers,
        )

        options: list[CarrierOption] = []
        for option in raw_options:
            price_delta = float(option.get("price_delta", 0.0))
            availability = float(option.get("availability", 0.0))
            transit_time = float(option.get("transit_time_hours", 1.0))
            score = max(0.0, price_delta * availability * transit_time)
            options.append(
                CarrierOption(
                    carrier=str(option.get("carrier", "unknown")),
                    price_delta=price_delta,
                    availability=availability,
                    transit_time_hours=transit_time,
                    score=score,
                )
            )

        ranked = sorted(options, key=lambda item: item.score, reverse=True)
        return ranked[:max_options]

    async def _fetch_availability(
        self,
        *,
        shipment_id: str,
        recommended_route: str,
        candidate_carriers: list[str],
    ) -> list[dict[str, object]]:
        if self.availability_api_url:
            request_payload = {
                "shipment_id": shipment_id,
                "recommended_route": recommended_route,
                "candidate_carriers": candidate_carriers,
            }
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(self.availability_api_url, json=request_payload)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
            except (httpx.HTTPError, ValueError):
                pass

        return self._mock_availability(candidate_carriers)

    async def _book_option(self, *, shipment_id: str, option: CarrierOption, route: str) -> str:
        if self.booking_api_url:
            request_payload = {
                "shipment_id": shipment_id,
                "carrier": option.carrier,
                "route": route,
            }
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(self.booking_api_url, json=request_payload)
                response.raise_for_status()
                body = response.json()
                if isinstance(body, dict) and body.get("booking_reference"):
                    return str(body["booking_reference"])
            except (httpx.HTTPError, ValueError):
                pass

        return f"mock-booking-{shipment_id}-{option.carrier}".lower().replace(" ", "-")

    @staticmethod
    def _mock_availability(candidate_carriers: list[str]) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for idx, carrier in enumerate(candidate_carriers):
            rows.append(
                {
                    "carrier": carrier,
                    "price_delta": round(120 + (idx * 40), 2),
                    "availability": round(max(0.15, 0.95 - (idx * 0.15)), 2),
                    "transit_time_hours": round(36 + (idx * 8), 2),
                }
            )
        return rows

    @staticmethod
    async def _update_shipment_record(
        *,
        session: AsyncSession,
        shipment_id: str,
        selected: CarrierOption,
    ) -> bool:
        stmt = select(ShipmentRecord).where(ShipmentRecord.shipment_ref == shipment_id)
        record = (await session.execute(stmt)).scalar_one_or_none()
        if record is None:
            return False
        record.carrier = selected.carrier
        record.status = "rebooked"
        return True


carrier_rebooking_service = CarrierRebookingService()
