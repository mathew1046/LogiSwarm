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

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import VesselPosition
from app.db.session import SessionLocal


class Anomaly(BaseModel):
    """Anomalous metric signal detected from rolling 7-day baseline statistics."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    metric: str
    current_value: float
    rolling_mean: float
    rolling_stddev: float
    rolling_p95: float
    z_score: float
    threshold: float = Field(default=2.5, ge=0.0)
    observed_at: datetime


class MetricSnapshot(BaseModel):
    """Computed rolling statistics and latest observation for a metric."""

    model_config = ConfigDict(extra="allow")

    metric: str
    current_value: float
    mean: float
    stddev: float
    p95: float
    observed_at: datetime


@dataclass(frozen=True)
class _MetricSpec:
    """Metadata that defines how each tracked metric is computed."""

    name: str


class TimeseriesState:
    """Short-term memory for rolling metric baselines and anomaly detection."""

    _EPSILON = 1e-9

    def __init__(
        self,
        region_id: str,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        lookback_days: int = 7,
        z_threshold: float = 2.5,
    ) -> None:
        self.region_id = region_id
        self.lookback_days = lookback_days
        self.z_threshold = z_threshold
        self.session_factory = session_factory or SessionLocal
        self.metrics = [
            _MetricSpec(name="vessel_queue_depth"),
            _MetricSpec(name="dwell_time_hours"),
            _MetricSpec(name="crane_utilization_pct"),
            _MetricSpec(name="weather_severity_score"),
        ]

    async def get_anomalies(self) -> list[Anomaly]:
        """Return all metric anomalies where z-score exceeds the configured threshold."""
        anomalies: list[Anomaly] = []

        async with self.session_factory() as session:
            for metric_spec in self.metrics:
                snapshot = await self._fetch_metric_snapshot(session=session, metric_spec=metric_spec)
                if snapshot is None:
                    continue

                z_score = self._z_score(
                    current_value=snapshot.current_value,
                    mean=snapshot.mean,
                    stddev=snapshot.stddev,
                )
                if z_score <= self.z_threshold:
                    continue

                anomalies.append(
                    Anomaly(
                        region_id=self.region_id,
                        metric=metric_spec.name,
                        current_value=snapshot.current_value,
                        rolling_mean=snapshot.mean,
                        rolling_stddev=snapshot.stddev,
                        rolling_p95=snapshot.p95,
                        z_score=z_score,
                        threshold=self.z_threshold,
                        observed_at=snapshot.observed_at,
                    )
                )

        return anomalies

    async def _fetch_metric_snapshot(
        self,
        session: AsyncSession,
        metric_spec: _MetricSpec,
    ) -> MetricSnapshot | None:
        cutoff = datetime.now(UTC) - timedelta(days=self.lookback_days)
        value_expr = self._metric_value_expr(metric_spec.name)

        filters = [
            VesselPosition.timestamp >= cutoff,
            VesselPosition.raw["region_id"].astext == self.region_id,
            value_expr.is_not(None),
        ]

        stats_stmt = select(
            func.avg(value_expr),
            func.coalesce(func.stddev_pop(value_expr), 0.0),
            func.percentile_cont(0.95).within_group(value_expr),
        ).where(*filters)

        stats_row = (await session.execute(stats_stmt)).one()
        rolling_mean = float(stats_row[0]) if stats_row[0] is not None else None
        rolling_stddev = float(stats_row[1]) if stats_row[1] is not None else 0.0
        rolling_p95 = float(stats_row[2]) if stats_row[2] is not None else 0.0

        if rolling_mean is None:
            return None

        current_stmt = (
            select(value_expr, VesselPosition.timestamp)
            .where(*filters)
            .order_by(VesselPosition.timestamp.desc())
            .limit(1)
        )
        current_row = (await session.execute(current_stmt)).first()
        if current_row is None or current_row[0] is None:
            return None

        observed_at = current_row[1]
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)

        return MetricSnapshot(
            metric=metric_spec.name,
            current_value=float(current_row[0]),
            mean=rolling_mean,
            stddev=rolling_stddev,
            p95=rolling_p95,
            observed_at=observed_at,
        )

    def _metric_value_expr(self, metric_name: str):
        if metric_name == "weather_severity_score":
            weather_numeric = self._numeric_json_value("weather_severity_score")
            weather_label = func.upper(VesselPosition.raw["weather_severity"].astext)
            weather_bucket = case(
                (weather_label.in_(["CRITICAL", "HIGH_RISK"]), 4.0),
                (weather_label == "HIGH", 3.0),
                (weather_label == "MEDIUM", 2.0),
                (weather_label == "LOW", 1.0),
                else_=None,
            )
            return func.coalesce(weather_numeric, weather_bucket)

        return self._numeric_json_value(metric_name)

    @staticmethod
    def _numeric_json_value(key: str):
        value_text = func.nullif(VesselPosition.raw[key].astext, "")
        is_numeric = value_text.op("~")(r"^-?\d+(\.\d+)?$")
        return case(
            (is_numeric, cast(value_text, Float)),
            else_=None,
        )

    def _z_score(self, current_value: float, mean: float, stddev: float) -> float:
        if stddev <= self._EPSILON:
            return 0.0
        return (current_value - mean) / stddev
