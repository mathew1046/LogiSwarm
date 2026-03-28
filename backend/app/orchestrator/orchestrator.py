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
import json
from collections import deque
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agents.agent_manager import NEIGHBOR_MAP
from app.bus.channels import ORCHESTRATOR_CASCADE_CHANNEL
from app.bus.connection import get_redis_client
from app.bus.publisher import publish
from app.orchestrator.escalation import EscalationDecision, EscalationEngine
from app.orchestrator.propagation_model import DisruptionPropagationModel, PropagationResult


class AgentAssessment(BaseModel):
    """Latest assessment published by an individual geo-agent."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    severity: str = "LOW"
    confidence: float = 0.0
    reasoning: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SwarmOrchestrator:
    """Supervisor that aggregates agent alerts and emits cross-region cascade events."""

    def __init__(self, correlation_interval_seconds: int = 60) -> None:
        self.correlation_interval_seconds = correlation_interval_seconds
        self.global_risk_map: dict[str, AgentAssessment] = {}
        self.risk_map_history: deque[dict[str, Any]] = deque(maxlen=2000)
        self._listener_task: asyncio.Task[None] | None = None
        self._correlation_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self.propagation_model = DisruptionPropagationModel()
        self.escalation_engine = EscalationEngine()

    async def start(self) -> None:
        """Start alert listener and periodic cross-region correlation loop."""
        if self._listener_task and not self._listener_task.done():
            return

        self._stop_event.clear()
        self._listener_task = asyncio.create_task(self._listen_agent_alerts(), name="orchestrator-listener")
        self._correlation_task = asyncio.create_task(self._correlation_loop(), name="orchestrator-correlation")

    async def stop(self) -> None:
        """Stop orchestrator background tasks gracefully."""
        self._stop_event.set()
        for task in (self._listener_task, self._correlation_task):
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._listener_task = None
        self._correlation_task = None

    async def _listen_agent_alerts(self) -> None:
        client = get_redis_client()
        pubsub = client.pubsub()
        pattern = "agent.*.alert"

        try:
            await pubsub.psubscribe(pattern)
            while not self._stop_event.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "pmessage":
                    payload = self._decode_payload(message.get("data"))
                    self._upsert_assessment(payload)
                await asyncio.sleep(0.05)
        finally:
            await pubsub.punsubscribe(pattern)
            await pubsub.aclose()
            await client.aclose()

    async def _correlation_loop(self) -> None:
        while not self._stop_event.is_set():
            await self.compute_cross_region_correlation()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.correlation_interval_seconds)
            except asyncio.TimeoutError:
                continue

    async def compute_cross_region_correlation(self) -> dict[str, Any]:
        """Compute adjacent-region clustering and emit cascade event when threshold is met."""
        high_regions = {
            region_id
            for region_id, assessment in self.global_risk_map.items()
            if assessment.severity.upper() in {"HIGH", "CRITICAL"}
        }

        active_clusters: list[tuple[str, str]] = []
        for region, neighbors in NEIGHBOR_MAP.items():
            if region not in high_regions:
                continue
            for neighbor in neighbors:
                if neighbor in high_regions:
                    pair = tuple(sorted((region, neighbor)))
                    if pair not in active_clusters:
                        active_clusters.append(pair)

        snapshot = {
            "timestamp": datetime.now(UTC).isoformat(),
            "active_regions": sorted(high_regions),
            "cluster_count": len(active_clusters),
            "clusters": [list(cluster) for cluster in active_clusters],
        }
        self.risk_map_history.append(snapshot)

        if len(active_clusters) >= 2:
            await publish(ORCHESTRATOR_CASCADE_CHANNEL, {
                "event_type": "cascade_cluster_detected",
                **snapshot,
            })

        return snapshot

    def get_global_risk_map(self) -> dict[str, dict[str, Any]]:
        """Return serializable global risk map snapshot."""
        return {
            region_id: assessment.model_dump(mode="json")
            for region_id, assessment in self.global_risk_map.items()
        }

    def get_risk_map_history(self, hours: int) -> list[dict[str, Any]]:
        """Return historical correlation snapshots limited by lookback window."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        output: list[dict[str, Any]] = []
        for row in self.risk_map_history:
            row_ts = self._parse_datetime(row.get("timestamp"))
            if row_ts >= cutoff:
                output.append(row)
        return output

    def cascade_risk(self, *, trigger_region: str, severity: str) -> PropagationResult:
        """Run propagation scoring for a trigger region/severity pair."""
        return self.propagation_model.propagate(
            trigger_region=trigger_region,
            severity=severity.upper(),
        )

    def evaluate_escalation(self, *, region_id: str, confidence: float, payload: dict[str, Any]) -> EscalationDecision:
        """Evaluate confidence-based escalation level with per-region overrides."""
        return self.escalation_engine.evaluate(
            region_id=region_id,
            confidence=confidence,
            payload=payload,
        )

    async def run_simulation(self, *, scenario: str, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """Replay historical scenario events and return detection-quality metrics."""
        scenario_key = scenario.strip().lower()
        events = self._scenario_events().get(scenario_key, [])

        detections = 0
        false_positives = 0
        first_alert_at: datetime | None = None
        replayed = 0

        for event in events:
            event_time = self._parse_datetime(event.get("timestamp"))
            if not (start_date <= event_time <= end_date):
                continue

            replayed += 1
            self._upsert_assessment(event)

            severity = str(event.get("severity") or "LOW").upper()
            confidence = float(event.get("confidence") or 0.0)
            if severity in {"HIGH", "CRITICAL"}:
                detections += 1
                if first_alert_at is None:
                    first_alert_at = event_time
            elif confidence >= 0.7:
                false_positives += 1

        baseline = max(replayed, 1)
        detection_rate = round(detections / baseline, 3)
        false_positive_rate = round(false_positives / baseline, 3)
        mean_time_to_alert_hours = 0.0
        if first_alert_at is not None:
            mean_time_to_alert_hours = round((first_alert_at - start_date).total_seconds() / 3600, 2)

        return {
            "scenario": scenario_key,
            "window": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "records_replayed": replayed,
            "metrics": {
                "detection_rate": detection_rate,
                "false_positive_rate": false_positive_rate,
                "mean_time_to_alert_hours": mean_time_to_alert_hours,
            },
        }

    def _upsert_assessment(self, payload: dict[str, Any]) -> None:
        region_id = str(payload.get("region_id") or "unknown")
        confidence_raw = payload.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        assessment = AgentAssessment(
            region_id=region_id,
            severity=str(payload.get("severity") or "LOW"),
            confidence=confidence,
            reasoning=str(payload.get("reasoning") or ""),
            recommended_actions=[str(item) for item in payload.get("recommended_actions", []) if isinstance(item, str)],
            updated_at=self._parse_datetime(payload.get("timestamp") or datetime.now(UTC).isoformat()),
        )
        self.global_risk_map[region_id] = assessment

    @staticmethod
    def _decode_payload(data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            return json.loads(data)
        if isinstance(data, bytes):
            return json.loads(data.decode("utf-8"))
        return {"raw": str(data)}

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str) and value:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = datetime.now(UTC)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @staticmethod
    def _scenario_events() -> dict[str, list[dict[str, Any]]]:
        return {
            "suez_2021": [
                {"region_id": "gulf_suez", "severity": "CRITICAL", "confidence": 0.92, "timestamp": "2021-03-23T10:00:00Z"},
                {"region_id": "se_asia", "severity": "HIGH", "confidence": 0.84, "timestamp": "2021-03-24T05:00:00Z"},
                {"region_id": "europe", "severity": "HIGH", "confidence": 0.87, "timestamp": "2021-03-25T07:00:00Z"},
            ],
            "covid_port_closures_2020": [
                {"region_id": "china_ea", "severity": "CRITICAL", "confidence": 0.9, "timestamp": "2020-02-01T08:00:00Z"},
                {"region_id": "se_asia", "severity": "HIGH", "confidence": 0.81, "timestamp": "2020-02-03T08:00:00Z"},
                {"region_id": "north_america", "severity": "MEDIUM", "confidence": 0.66, "timestamp": "2020-02-06T08:00:00Z"},
            ],
            "la_port_backlog_2021": [
                {"region_id": "north_america", "severity": "HIGH", "confidence": 0.83, "timestamp": "2021-10-01T09:00:00Z"},
                {"region_id": "europe", "severity": "MEDIUM", "confidence": 0.58, "timestamp": "2021-10-06T09:00:00Z"},
            ],
        }

swarm_orchestrator = SwarmOrchestrator()
