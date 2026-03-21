from __future__ import annotations

import os
import random
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class PortSensorSnapshot(BaseModel):
    """Normalized mock port sensor snapshot for a single port node."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    port_id: str
    crane_utilization_pct: float = Field(ge=0.0, le=100.0)
    vessel_queue_depth: int = Field(ge=0)
    gate_throughput: float = Field(ge=0.0)
    dwell_time_hours: float = Field(ge=0.0)
    timestamp: datetime
    anomaly_type: str | None = None


class PortSensorSimulator:
    """Generate realistic mock port telemetry with occasional anomaly spikes."""

    def __init__(self, anomaly_probability: float = 0.12) -> None:
        self.mock_enabled = self._to_bool(os.getenv("PORT_MOCK_ENABLED", "true"))
        self.anomaly_probability = anomaly_probability

    async def fetch(
        self,
        region_id: str,
        port_ids: list[str] | None = None,
    ) -> list[PortSensorSnapshot]:
        """Return simulated snapshots for each requested port in the region."""
        if not self.mock_enabled:
            return []

        ports = port_ids or self._default_ports(region_id=region_id)
        now = datetime.now(UTC)

        snapshots: list[PortSensorSnapshot] = []
        for port_id in ports:
            snapshots.append(self._build_snapshot(region_id=region_id, port_id=port_id, timestamp=now))

        return snapshots

    def _build_snapshot(
        self,
        region_id: str,
        port_id: str,
        timestamp: datetime,
    ) -> PortSensorSnapshot:
        crane_utilization_pct = round(random.uniform(55.0, 88.0), 2)
        vessel_queue_depth = random.randint(4, 18)
        gate_throughput = round(random.uniform(85.0, 240.0), 2)
        dwell_time_hours = round(random.uniform(8.0, 28.0), 2)

        anomaly_type: str | None = None
        if random.random() < self.anomaly_probability:
            (
                crane_utilization_pct,
                vessel_queue_depth,
                gate_throughput,
                dwell_time_hours,
                anomaly_type,
            ) = self._inject_anomaly(
                crane_utilization_pct=crane_utilization_pct,
                vessel_queue_depth=vessel_queue_depth,
                gate_throughput=gate_throughput,
                dwell_time_hours=dwell_time_hours,
            )

        return PortSensorSnapshot(
            region_id=region_id,
            port_id=port_id,
            crane_utilization_pct=crane_utilization_pct,
            vessel_queue_depth=vessel_queue_depth,
            gate_throughput=gate_throughput,
            dwell_time_hours=dwell_time_hours,
            timestamp=timestamp,
            anomaly_type=anomaly_type,
        )

    @staticmethod
    def _inject_anomaly(
        crane_utilization_pct: float,
        vessel_queue_depth: int,
        gate_throughput: float,
        dwell_time_hours: float,
    ) -> tuple[float, int, float, float, str]:
        anomaly = random.choice(
            [
                "CRANE_IDLE_6H",
                "QUEUE_DEPTH_3X",
                "GATE_THROUGHPUT_DROP",
                "DWELL_TIME_SURGE",
            ]
        )

        if anomaly == "CRANE_IDLE_6H":
            crane_utilization_pct = round(random.uniform(0.0, 8.0), 2)
            dwell_time_hours = max(dwell_time_hours, 6.0)
        elif anomaly == "QUEUE_DEPTH_3X":
            vessel_queue_depth = max(vessel_queue_depth * 3, 30)
            dwell_time_hours = round(max(dwell_time_hours, random.uniform(24.0, 54.0)), 2)
        elif anomaly == "GATE_THROUGHPUT_DROP":
            gate_throughput = round(random.uniform(18.0, 50.0), 2)
            vessel_queue_depth = max(vessel_queue_depth, random.randint(20, 42))
        else:
            dwell_time_hours = round(random.uniform(48.0, 96.0), 2)
            crane_utilization_pct = round(min(crane_utilization_pct, random.uniform(15.0, 40.0)), 2)

        return (
            crane_utilization_pct,
            vessel_queue_depth,
            gate_throughput,
            dwell_time_hours,
            anomaly,
        )

    @staticmethod
    def _default_ports(region_id: str) -> list[str]:
        slug = region_id.lower().replace(" ", "-")
        return [
            f"{slug}-port-alpha",
            f"{slug}-port-bravo",
            f"{slug}-port-charlie",
        ]

    @staticmethod
    def _to_bool(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "on"}
