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

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.email_notifier import EmailNotifier, email_notifier
from app.actions.slack_notifier import SlackNotifier, slack_notifier
from app.bus.channels import ORCHESTRATOR_CASCADE_CHANNEL
from app.bus.connection import get_redis_client
from app.bus.publisher import publish
from app.db.models import ShipmentRecord
from app.db.session import get_db_session
from app.orchestrator.orchestrator import SwarmOrchestrator, swarm_orchestrator

logger = logging.getLogger(__name__)

ETA_RECALC_CHANNEL = "eta_recalc.updated"


class ETAMessage(BaseModel):
    """Payload for ETA update notifications."""

    model_config = ConfigDict(extra="allow")

    shipment_id: str
    shipment_ref: str
    original_eta: datetime | None
    predicted_eta: datetime
    delay_hours: float
    disrupted_regions: list[str]
    cascade_score: float
    recalculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ETANotificationPayload(BaseModel):
    """Structured ETA change notification for email/Slack dispatch."""

    shipment_ref: str = Field(min_length=1)
    carrier: str | None = None
    origin: str | None = None
    destination: str | None = None
    original_eta: datetime | None = None
    predicted_eta: datetime
    delay_hours: float = Field(ge=0.0)
    disrupted_regions: list[str] = Field(default_factory=list)
    cascade_score: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)


class ETARecalculator:
    """Recalculate ETAs for shipments affected by disruptions and send notifications."""

    def __init__(
        self,
        orchestrator: SwarmOrchestrator | None = None,
        slack: SlackNotifier | None = None,
        email: EmailNotifier | None = None,
    ) -> None:
        self.orchestrator = orchestrator or swarm_orchestrator
        self.slack = slack or slack_notifier
        self.email = email or email_notifier
        self._stop_event = asyncio.Event()
        self._listener_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start listening for HIGH/CRITICAL disruption events."""
        if self._listener_task and not self._listener_task.done():
            return

        self._stop_event.clear()
        self._listener_task = asyncio.create_task(
            self._listen_disruptions(), name="eta-recalc-listener"
        )
        logger.info("ETA recalculation listener started")

    async def stop(self) -> None:
        """Stop the listener gracefully."""
        self._stop_event.set()
        if self._listener_task is None:
            return
        self._listener_task.cancel()
        try:
            await self._listener_task
        except asyncio.CancelledError:
            pass
        self._listener_task = None
        logger.info("ETA recalculation listener stopped")

    async def _listen_disruptions(self) -> None:
        """Subscribe to agent alerts and orchestration cascade events."""
        client = get_redis_client()
        pubsub = client.pubsub()
        patterns = ["agent.*.alert", ORCHESTRATOR_CASCADE_CHANNEL]

        try:
            await pubsub.psubscribe(*patterns)
            while not self._stop_event.is_set():
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message.get("type") == "pmessage":
                    await self._handle_disruption_message(message)
                await asyncio.sleep(0.05)
        finally:
            await pubsub.punsubscribe(*patterns)
            await pubsub.aclose()
            await client.aclose()

    async def _handle_disruption_message(self, message: dict[str, Any]) -> None:
        """Process incoming disruption alerts and trigger ETA recalculation."""
        try:
            payload = self._decode_payload(message.get("data"))
            severity = str(payload.get("severity", "LOW")).upper()

            if severity not in {"HIGH", "CRITICAL"}:
                return

            region_id = str(payload.get("region_id") or "unknown")
            confidence = float(payload.get("confidence", 0.0))

            await self.recalculate_etas_for_region(
                region_id=region_id,
                severity=severity,
                cascade_score=confidence,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Failed to handle disruption message: {exc}")

    async def recalculate_etas_for_region(
        self,
        region_id: str,
        severity: str,
        cascade_score: float,
    ) -> list[ETAMessage]:
        """Find shipments passing through disrupted region and update their ETAs."""
        async for session in get_db_session():
            return await self._do_recalculate(
                session, region_id, severity, cascade_score
            )
        return []

    async def _do_recalculate(
        self,
        session: AsyncSession,
        region_id: str,
        severity: str,
        cascade_score: float,
    ) -> list[ETAMessage]:
        """Execute ETA recalculation and notification."""
        impacted_shipments = await self._find_shipments_in_region(session, region_id)

        if not impacted_shipments:
            logger.debug(f"No shipments found in region {region_id}")
            return []

        propagation = self.orchestrator.cascade_risk(
            trigger_region=region_id, severity=severity
        )

        delay_multiplier = self._severity_delay_multiplier(severity)
        delay_hours = round(
            propagation.estimated_delay_propagation_hours
            * delay_multiplier
            * cascade_score,
            2,
        )

        messages: list[ETAMessage] = []
        notifications: list[tuple[ShipmentRecord, ETAMessage]] = []

        for shipment in impacted_shipments:
            msg = await self._update_shipment_eta(
                session=session,
                shipment=shipment,
                delay_hours=delay_hours,
                disrupted_regions=[region_id],
                cascade_score=cascade_score,
            )
            if msg:
                messages.append(msg)
                notifications.append((shipment, msg))

        await session.commit()

        for shipment, msg in notifications:
            await self._send_notifications(shipment=shipment, message=msg)

        logger.info(
            f"Recalculated ETAs for {len(messages)} shipments in region {region_id}, "
            f"delay={delay_hours}h"
        )
        return messages

    async def _find_shipments_in_region(
        self, session: AsyncSession, region_id: str
    ) -> list[ShipmentRecord]:
        """Query shipments whose route includes the disrupted region."""
        stmt = select(ShipmentRecord).where(
            ShipmentRecord.route["regions"].astext.contains(region_id),
            ShipmentRecord.status.not_in({"delivered", "cancelled"}),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _update_shipment_eta(
        self,
        session: AsyncSession,
        shipment: ShipmentRecord,
        delay_hours: float,
        disrupted_regions: list[str],
        cascade_score: float,
        threshold_hours: float = 1.0,
    ) -> ETAMessage | None:
        """Update shipment's predicted ETA and delay hours, and publish update."""
        original_eta = shipment.eta
        base_eta = original_eta or datetime.now(UTC)
        predicted_eta = base_eta + timedelta(hours=delay_hours)

        shipment.predicted_eta = predicted_eta
        shipment.delay_hours = delay_hours
        shipment.updated_at = datetime.now(UTC)

        await publish(
            ETA_RECALC_CHANNEL,
            {
                "event_type": "eta_updated",
                "shipment_id": str(shipment.id),
                "delay_hours": delay_hours,
                "disrupted_regions": disrupted_regions,
                "cascade_score": cascade_score,
                "predicted_eta": predicted_eta.isoformat(),
            },
        )

        return ETAMessage(
            shipment_id=str(shipment.id),
            shipment_ref=shipment.shipment_ref,
            original_eta=original_eta,
            predicted_eta=predicted_eta,
            delay_hours=delay_hours,
            disrupted_regions=disrupted_regions,
            cascade_score=cascade_score,
        )

    async def _send_notifications(
        self, shipment: ShipmentRecord, message: ETAMessage
    ) -> None:
        """Send ETA change notifications via Slack and email."""
        carrier = (
            message.shipment_ref.split("-")[0]
            if "-" in message.shipment_ref
            else shipment.carrier
        )

        eta_payload = ETANotificationPayload(
            shipment_ref=shipment.shipment_ref,
            carrier=carrier,
            origin=shipment.origin,
            destination=shipment.destination,
            original_eta=message.original_eta,
            predicted_eta=message.predicted_eta,
            delay_hours=message.delay_hours,
            disrupted_regions=message.disrupted_regions,
            cascade_score=message.cascade_score,
            confidence=0.85,
        )

        slack_result = await self.slack.send_alert(
            self._build_slack_eta_alert(eta_payload)
        )
        if not slack_result.ok:
            logger.warning(
                f"Slack ETA notification failed: {slack_result.response_body}"
            )

        email_result = await self.email.send_alert(
            self._build_email_eta_alert(eta_payload)
        )
        if not email_result.ok:
            logger.warning(f"Email ETA notification failed: {email_result.error}")

    def _build_slack_eta_alert(
        self, payload: ETANotificationPayload
    ) -> "app.actions.slack_notifier.SlackAlertPayload":
        from app.actions.slack_notifier import SlackAlertPayload

        delay_str = (
            f"{int(payload.delay_hours)}h {int((payload.delay_hours % 1) * 60)}m"
            if payload.delay_hours >= 1
            else f"{int(payload.delay_hours * 60)}m"
        )
        predicted_str = payload.predicted_eta.strftime("%Y-%m-%d %H:%M UTC")
        original_str = (
            payload.original_eta.strftime("%Y-%m-%d %H:%M UTC")
            if payload.original_eta
            else "Unknown"
        )
        origin = payload.origin or "Unknown"
        destination = payload.destination or "Unknown"

        return SlackAlertPayload(
            project_id="eta-recalculation",
            region_id=payload.disrupted_regions[0]
            if payload.disrupted_regions
            else "unknown",
            severity="HIGH",
            affected_routes=[f"{origin} → {destination}"],
            top_recommendation=f"ETA updated: {predicted_str} (+{delay_str})",
            confidence=payload.confidence,
            reason=f"Disruption detected in {', '.join(payload.disrupted_regions)}. "
            f"Original ETA: {original_str}. Delay: {delay_str}.",
            triggered_by=f"shipment:{payload.shipment_ref}",
        )

    def _build_email_eta_alert(
        self, payload: ETANotificationPayload
    ) -> "app.actions.email_notifier.EmailAlertPayload":
        from app.actions.email_notifier import EmailAlertPayload

        delay_str = (
            f"{int(payload.delay_hours)} hours {int((payload.delay_hours % 1) * 60)} minutes"
            if payload.delay_hours >= 1
            else f"{int(payload.delay_hours * 60)} minutes"
        )
        predicted_str = payload.predicted_eta.strftime("%Y-%m-%d %H:%M UTC")
        original_str = (
            payload.original_eta.strftime("%Y-%m-%d %H:%M UTC")
            if payload.original_eta
            else "Unknown"
        )

        return EmailAlertPayload(
            project_id="eta-recalculation",
            region_id=payload.disrupted_regions[0]
            if payload.disrupted_regions
            else "unknown",
            severity="HIGH",
            affected_regions=payload.disrupted_regions,
            route_recommendations=[
                f"Shipment {payload.shipment_ref}: ETA updated to {predicted_str}",
                f"Original ETA: {original_str}",
                f"Delay: {delay_str}",
            ],
            propagation_forecast=f"Cascade score: {payload.cascade_score:.2%}",
            confidence=payload.confidence,
            reason=f"Disruption detected in {', '.join(payload.disrupted_regions)}. "
            f"Shipment route affected. ETA recalculated.",
            recipients=[],
        )

    @staticmethod
    def _severity_delay_multiplier(severity: str) -> float:
        multipliers = {
            "LOW": 0.5,
            "MEDIUM": 1.0,
            "HIGH": 1.5,
            "CRITICAL": 2.5,
        }
        return multipliers.get(severity.upper(), 1.0)

    @staticmethod
    def _decode_payload(data: Any) -> dict[str, Any]:
        import json

        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            return json.loads(data)
        if isinstance(data, bytes):
            return json.loads(data.decode("utf-8"))
        return {"raw": str(data)}


eta_recalculator = ETARecalculator()
