from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_manager import agent_manager
from app.agents.timeseries_state import TimeseriesState
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


class MetricThresholdConfig(BaseModel):
    """Threshold configuration for a single metric."""

    model_config = ConfigDict(extra="allow")

    metric: str
    z_threshold: float = Field(ge=0.0, le=10.0)
    enabled: bool = True
    adaptive_adjustment: bool = True


class AnomalyConfigResponse(BaseModel):
    """Response containing all anomaly configuration for a region."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    thresholds: list[MetricThresholdConfig]
    lookback_days: int
    adaptive_tuning_enabled: bool
    false_positive_count_30d: int


class AnomalyConfigUpdate(BaseModel):
    """Request body for updating anomaly detection thresholds."""

    thresholds: list[MetricThresholdConfig] | None = None
    lookback_days: int | None = Field(default=None, ge=1, le=30)
    adaptive_tuning_enabled: bool | None = None


class AnomalyHistoryEntry(BaseModel):
    """A single anomaly detection event in history."""

    model_config = ConfigDict(extra="allow")

    id: str
    region_id: str
    metric: str
    z_score: float
    threshold: float
    current_value: float
    rolling_mean: float
    detected_at: datetime
    false_positive: bool = False
    confirmed_at: datetime | None = None


class AnomalyHistoryResponse(BaseModel):
    """Paginated response of anomaly history."""

    model_config = ConfigDict(extra="allow")

    anomalies: list[AnomalyHistoryEntry]
    total: int
    limit: int
    offset: int


class FalsePositiveMarkRequest(BaseModel):
    """Request body for marking an anomaly as false positive."""

    reason: str | None = Field(default=None, max_length=500)


class FalsePositiveMarkResponse(BaseModel):
    """Response after marking an anomaly as false positive."""

    model_config = ConfigDict(extra="allow")

    anomaly_id: str
    region_id: str
    metric: str
    old_threshold: float
    new_threshold: float
    adjustment_reason: str


_region_anomaly_configs: dict[str, dict[str, Any]] = {}
_anomaly_history: dict[str, list[dict[str, Any]]] = {}
_false_positive_marks: dict[str, dict[str, bool]] = {}

DEFAULT_THRESHOLDS: dict[str, float] = {
    "vessel_queue_depth": 2.5,
    "dwell_time_hours": 2.5,
    "crane_utilization_pct": 2.0,
    "weather_severity_score": 3.0,
}

ADJUSTMENT_FACTOR = 0.25


def _get_region_config(region_id: str) -> dict[str, Any]:
    if region_id not in _region_anomaly_configs:
        _region_anomaly_configs[region_id] = {
            "thresholds": {
                metric: {
                    "threshold": default,
                    "enabled": True,
                    "adaptive_adjustment": True,
                }
                for metric, default in DEFAULT_THRESHOLDS.items()
            },
            "lookback_days": 7,
            "adaptive_tuning_enabled": True,
        }
    return _region_anomaly_configs[region_id]


@router.get("/{region_id}/config", response_model=AnomalyConfigResponse)
async def get_anomaly_config(region_id: str) -> AnomalyConfigResponse:
    """Get current anomaly detection thresholds and configuration for a region."""
    try:
        agent_manager.get_agent(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None

    config = _get_region_config(region_id)
    thresholds: list[MetricThresholdConfig] = []

    for metric, settings in config["thresholds"].items():
        thresholds.append(
            MetricThresholdConfig(
                metric=metric,
                z_threshold=settings["threshold"],
                enabled=settings["enabled"],
                adaptive_adjustment=settings["adaptive_adjustment"],
            )
        )

    fp_count = len(
        [
            a
            for a in _anomaly_history.get(region_id, [])
            if _false_positive_marks.get(region_id, {}).get(a.get("id", ""), False)
        ]
    )

    return AnomalyConfigResponse(
        region_id=region_id,
        thresholds=thresholds,
        lookback_days=config["lookback_days"],
        adaptive_tuning_enabled=config["adaptive_tuning_enabled"],
        false_positive_count_30d=fp_count,
    )


@router.put("/{region_id}/config", response_model=AnomalyConfigResponse)
async def update_anomaly_config(
    region_id: str,
    payload: AnomalyConfigUpdate,
) -> AnomalyConfigResponse:
    """Update anomaly detection thresholds and configuration for a region."""
    try:
        agent_manager.get_agent(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None

    config = _get_region_config(region_id)

    if payload.thresholds is not None:
        for threshold_config in payload.thresholds:
            metric = threshold_config.metric
            if metric in config["thresholds"]:
                config["thresholds"][metric]["threshold"] = threshold_config.z_threshold
                config["thresholds"][metric]["enabled"] = threshold_config.enabled
                config["thresholds"][metric]["adaptive_adjustment"] = (
                    threshold_config.adaptive_adjustment
                )

    if payload.lookback_days is not None:
        config["lookback_days"] = payload.lookback_days

    if payload.adaptive_tuning_enabled is not None:
        config["adaptive_tuning_enabled"] = payload.adaptive_tuning_enabled

    logger.info(
        f"Updated anomaly config for region {region_id}: {payload.model_dump(exclude_none=True)}"
    )

    return await get_anomaly_config(region_id)


@router.get("/{region_id}/history", response_model=AnomalyHistoryResponse)
async def get_anomaly_history(
    region_id: str,
    days: int = Query(default=30, ge=1, le=90),
    metric: str | None = Query(default=None),
    confirmed_only: bool = Query(default=False),
    false_positives_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AnomalyHistoryResponse:
    """Get past anomaly detections with optional filtering."""
    try:
        agent_manager.get_agent(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None

    history = _anomaly_history.get(region_id, [])
    cutoff = datetime.now(UTC) - timedelta(days=days)

    filtered: list[dict[str, Any]] = []
    for entry in history:
        entry_time = entry.get("detected_at")
        if isinstance(entry_time, str):
            entry_time = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
        if entry_time and entry_time < cutoff:
            continue

        if metric and entry.get("metric") != metric:
            continue

        is_fp = _false_positive_marks.get(region_id, {}).get(entry.get("id", ""), False)

        if confirmed_only and is_fp:
            continue
        if false_positives_only and not is_fp:
            continue

        entry_copy = entry.copy()
        entry_copy["false_positive"] = is_fp
        filtered.append(entry_copy)

    total = len(filtered)
    paginated = filtered[offset : offset + limit]

    anomalies: list[AnomalyHistoryEntry] = []
    for entry in paginated:
        detected_at_raw = entry.get("detected_at")
        if isinstance(detected_at_raw, str):
            detected_at = datetime.fromisoformat(detected_at_raw.replace("Z", "+00:00"))
        else:
            detected_at = detected_at_raw or datetime.now(UTC)

        anomalies.append(
            AnomalyHistoryEntry(
                id=entry.get("id", "unknown"),
                region_id=entry.get("region_id", region_id),
                metric=entry.get("metric", "unknown"),
                z_score=entry.get("z_score", 0.0),
                threshold=entry.get("threshold", 2.5),
                current_value=entry.get("current_value", 0.0),
                rolling_mean=entry.get("rolling_mean", 0.0),
                detected_at=detected_at,
                false_positive=entry.get("false_positive", False),
                confirmed_at=entry.get("confirmed_at"),
            )
        )

    return AnomalyHistoryResponse(
        anomalies=anomalies,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{region_id}/history/{anomaly_id}/false-positive",
    response_model=FalsePositiveMarkResponse,
)
async def mark_anomaly_false_positive(
    region_id: str,
    anomaly_id: str,
    payload: FalsePositiveMarkRequest,
) -> FalsePositiveMarkResponse:
    """Mark an anomaly as false positive and adjust threshold (adaptive tuning)."""
    try:
        agent_manager.get_agent(region_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Agent '{region_id}' not found"
        ) from None

    history = _anomaly_history.get(region_id, [])
    anomaly_entry: dict[str, Any] | None = None

    for entry in history:
        if entry.get("id") == anomaly_id:
            anomaly_entry = entry
            break

    if anomaly_entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Anomaly '{anomaly_id}' not found in region '{region_id}'",
        )

    if region_id not in _false_positive_marks:
        _false_positive_marks[region_id] = {}
    _false_positive_marks[region_id][anomaly_id] = True

    config = _get_region_config(region_id)
    metric = anomaly_entry.get("metric", "")
    adaptive_enabled = config.get("adaptive_tuning_enabled", True)

    old_threshold = config["thresholds"].get(metric, {}).get("threshold", 2.5)
    new_threshold = old_threshold

    if adaptive_enabled and metric in config["thresholds"]:
        if config["thresholds"][metric].get("adaptive_adjustment", True):
            delta = anomaly_entry.get("z_score", old_threshold) - old_threshold
            new_threshold = round(old_threshold + (delta * ADJUSTMENT_FACTOR) + 0.5, 2)
            new_threshold = max(1.0, min(10.0, new_threshold))
            config["thresholds"][metric]["threshold"] = new_threshold

            logger.info(
                f"Adaptive threshold adjustment for {region_id}/{metric}: "
                f"{old_threshold} → {new_threshold} (FP marked: {anomaly_id})"
            )

    adjustment_reason = "false_positive_marked"
    if payload.reason:
        adjustment_reason = f"false_positive: {payload.reason}"

    return FalsePositiveMarkResponse(
        anomaly_id=anomaly_id,
        region_id=region_id,
        metric=metric,
        old_threshold=old_threshold,
        new_threshold=new_threshold,
        adjustment_reason=adjustment_reason,
    )


def record_anomaly(
    region_id: str,
    metric: str,
    z_score: float,
    threshold: float,
    current_value: float,
    rolling_mean: float,
) -> str:
    """Record an anomaly detection event (called by TimeseriesState)."""
    import uuid

    anomaly_id = str(uuid.uuid4())
    entry = {
        "id": anomaly_id,
        "region_id": region_id,
        "metric": metric,
        "z_score": z_score,
        "threshold": threshold,
        "current_value": current_value,
        "rolling_mean": rolling_mean,
        "detected_at": datetime.now(UTC).isoformat(),
        "confirmed_at": None,
    }

    if region_id not in _anomaly_history:
        _anomaly_history[region_id] = []
    _anomaly_history[region_id].append(entry)

    cutoff = datetime.now(UTC) - timedelta(days=90)
    _anomaly_history[region_id] = [
        e
        for e in _anomaly_history[region_id]
        if datetime.fromisoformat(e["detected_at"].replace("Z", "+00:00")) >= cutoff
    ]

    return anomaly_id
