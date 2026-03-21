from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict


RETRYABLE_STATUS_CODES = {429, 503}


class CarrierShipmentUpdate(BaseModel):
    """Normalized carrier shipment payload used by geo-agents."""

    model_config = ConfigDict(extra="allow")

    shipment_id: str
    carrier: str
    origin: str
    destination: str
    eta: datetime
    status: str
    delay_hours: float
    customs_hold: bool


class CarrierConnector:
    """Fetch shipment ETA/customs data from Maersk or a generic carrier endpoint."""

    def __init__(
        self,
        maersk_base_url: str = "https://api.maersk.com/track/v1",
        generic_base_url: str = "https://api.example-carrier.com/v1",
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self.maersk_base_url = maersk_base_url.rstrip("/")
        self.generic_base_url = generic_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    async def fetch_shipments(
        self,
        shipment_ids: list[str],
        carrier: str = "maersk",
        api_key: str | None = None,
    ) -> list[CarrierShipmentUpdate]:
        """Fetch normalized updates from the preferred carrier API with REST fallback."""
        if not shipment_ids:
            return []

        normalized_carrier = carrier.strip().lower()
        if normalized_carrier == "maersk":
            try:
                return await self._fetch_maersk(shipment_ids=shipment_ids, api_key=api_key)
            except Exception:
                return await self._fetch_generic(
                    shipment_ids=shipment_ids,
                    carrier=carrier,
                    api_key=api_key,
                )

        return await self._fetch_generic(
            shipment_ids=shipment_ids,
            carrier=carrier,
            api_key=api_key,
        )

    async def _fetch_maersk(
        self,
        shipment_ids: list[str],
        api_key: str | None,
    ) -> list[CarrierShipmentUpdate]:
        endpoint = f"{self.maersk_base_url}/shipments"
        headers = self._build_headers(api_key=api_key)
        params = {"shipment_ids": ",".join(shipment_ids)}

        payload = await self._request_json_with_retry(
            method="GET",
            url=endpoint,
            headers=headers,
            params=params,
        )
        items = self._extract_items(payload)

        updates: list[CarrierShipmentUpdate] = []
        for item in items:
            shipment_id = str(item.get("shipment_id") or item.get("reference") or "")
            if not shipment_id:
                continue

            eta = self._parse_datetime(item.get("eta") or item.get("estimated_arrival"))
            delay_hours = self._parse_delay_hours(item=item, eta=eta)
            customs_hold = self._parse_customs_hold(item)
            status = self._parse_status(item=item, delay_hours=delay_hours)

            updates.append(
                CarrierShipmentUpdate(
                    shipment_id=shipment_id,
                    carrier="maersk",
                    origin=str(item.get("origin") or item.get("origin_port") or "UNKNOWN"),
                    destination=str(
                        item.get("destination") or item.get("destination_port") or "UNKNOWN"
                    ),
                    eta=eta,
                    status=status,
                    delay_hours=delay_hours,
                    customs_hold=customs_hold,
                )
            )

        return updates

    async def _fetch_generic(
        self,
        shipment_ids: list[str],
        carrier: str,
        api_key: str | None,
    ) -> list[CarrierShipmentUpdate]:
        endpoint = f"{self.generic_base_url}/shipments/track"
        headers = self._build_headers(api_key=api_key)
        payload = {"shipment_ids": shipment_ids, "carrier": carrier}

        response_payload = await self._request_json_with_retry(
            method="POST",
            url=endpoint,
            headers=headers,
            json_payload=payload,
        )
        items = self._extract_items(response_payload)

        updates: list[CarrierShipmentUpdate] = []
        for item in items:
            shipment_id = str(item.get("shipment_id") or item.get("id") or "")
            if not shipment_id:
                continue

            eta = self._parse_datetime(item.get("eta") or item.get("predicted_eta"))
            delay_hours = self._parse_delay_hours(item=item, eta=eta)
            customs_hold = self._parse_customs_hold(item)
            status = self._parse_status(item=item, delay_hours=delay_hours)

            updates.append(
                CarrierShipmentUpdate(
                    shipment_id=shipment_id,
                    carrier=str(item.get("carrier") or carrier or "generic"),
                    origin=str(item.get("origin") or item.get("from") or "UNKNOWN"),
                    destination=str(item.get("destination") or item.get("to") or "UNKNOWN"),
                    eta=eta,
                    status=status,
                    delay_hours=delay_hours,
                    customs_hold=customs_hold,
                )
            )

        return updates

    async def _request_json_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, str] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_payload,
                    )

                if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    await asyncio.sleep(self.backoff_seconds * (2**attempt))
                    continue

                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, list):
                    return payload
                if isinstance(payload, dict):
                    return payload
                return {}
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    await asyncio.sleep(self.backoff_seconds * (2**attempt))
                    continue
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(self.backoff_seconds * (2**attempt))
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Carrier request failed without explicit exception")

    @staticmethod
    def _extract_items(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        shipments = payload.get("shipments")
        if isinstance(shipments, list):
            return [item for item in shipments if isinstance(item, dict)]

        return []

    @staticmethod
    def _build_headers(api_key: str | None) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    @staticmethod
    def _parse_delay_hours(item: dict[str, Any], eta: datetime) -> float:
        raw_delay = item.get("delay_hours")
        if raw_delay is not None:
            return float(raw_delay)

        planned_eta_value = item.get("planned_eta") or item.get("original_eta")
        if planned_eta_value is not None:
            planned_eta = CarrierConnector._parse_datetime(planned_eta_value)
            delay = (eta - planned_eta).total_seconds() / 3600
            return round(max(delay, 0.0), 2)

        reported_delay = item.get("delay")
        if isinstance(reported_delay, (int, float)):
            return float(reported_delay)

        return 0.0

    @staticmethod
    def _parse_customs_hold(item: dict[str, Any]) -> bool:
        raw_value = item.get("customs_hold")
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, str):
            return raw_value.strip().lower() in {"1", "true", "yes", "hold", "on_hold"}

        status = str(item.get("customs_status") or "").strip().lower()
        return status in {"hold", "on_hold", "inspection", "blocked"}

    @staticmethod
    def _parse_status(item: dict[str, Any], delay_hours: float) -> str:
        if delay_hours > 24:
            return "DELAY_ALERT"

        candidate = item.get("status") or item.get("shipment_status") or "IN_TRANSIT"
        return str(candidate)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str) and value:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(float(value), tz=UTC)
        else:
            dt = datetime.now(UTC) + timedelta(days=5)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
