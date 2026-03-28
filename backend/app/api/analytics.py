from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.projects import Envelope, EnvelopeMeta

router = APIRouter(prefix="/analytics", tags=["analytics"])


TimeRange = Literal["7d", "30d", "90d", "custom"]


class DisruptionTimelinePoint(BaseModel):
    """A single point in the disruption timeline."""

    model_config = ConfigDict(extra="allow")

    date: str
    region_id: str
    region_name: str
    count: int
    severity: str


class SeverityDistribution(BaseModel):
    """Severity distribution for donut chart."""

    model_config = ConfigDict(extra="allow")

    severity: str
    count: int
    percentage: float


class RegionMetric(BaseModel):
    """Metrics for a single region."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    region_name: str
    disruption_count: int
    mean_time_to_detection_hours: float
    auto_act_count: int
    recommend_count: int
    monitor_count: int
    accuracy_score: float


class DecisionBreakdown(BaseModel):
    """Decision type breakdown."""

    model_config = ConfigDict(extra="allow")

    auto_act: int
    recommend: int
    monitor: int
    total: int


class AccuracyTimelinePoint(BaseModel):
    """Accuracy score over time."""

    model_config = ConfigDict(extra="allow")

    date: str
    region_id: str
    accuracy_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class AnalyticsSummary(BaseModel):
    """Summary statistics."""

    model_config = ConfigDict(extra="allow")

    total_disruptions: int
    total_regions: int
    overall_accuracy: float
    avg_time_to_detection_hours: float
    decision_breakdown: DecisionBreakdown


class AnalyticsResponse(BaseModel):
    """Full analytics response."""

    model_config = ConfigDict(extra="allow")

    timeline: list[DisruptionTimelinePoint]
    severity_distribution: list[SeverityDistribution]
    region_metrics: list[RegionMetric]
    accuracy_timeline: list[AccuracyTimelinePoint]
    summary: AnalyticsSummary


_disruption_store: list[dict[str, Any]] = []
_decision_store: list[dict[str, Any]] = []
_accuracy_store: list[dict[str, Any]] = []


def _generate_mock_data() -> None:
    """Generate mock analytics data for demonstration."""
    global _disruption_store, _decision_store, _accuracy_store

    if _disruption_store:
        return

    regions = [
        {"id": "se_asia", "name": "Southeast Asia"},
        {"id": "europe", "name": "Europe"},
        {"id": "gulf_suez", "name": "Gulf/Suez"},
        {"id": "north_america", "name": "North America"},
        {"id": "china_ea", "name": "China/East Asia"},
    ]

    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    now = datetime.now(UTC)

    for i in range(90):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        for region in regions:
            import random

            count = random.randint(0, 5)
            if count > 0:
                _disruption_store.append(
                    {
                        "date": date,
                        "region_id": region["id"],
                        "region_name": region["name"],
                        "count": count,
                        "severity": random.choice(severities),
                        "detected_at": (
                            now - timedelta(days=i, hours=random.randint(0, 23))
                        ).isoformat(),
                    }
                )

    for i in range(200):
        _decision_store.append(
            {
                "region_id": random.choice(regions)["id"],
                "decision_type": random.choice(["auto_act", "recommend", "monitor"]),
                "timestamp": (now - timedelta(days=random.randint(0, 89))).isoformat(),
                "correct": random.random() > 0.15,
            }
        )

    for i in range(90):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        for region in regions:
            import random

            _accuracy_store.append(
                {
                    "date": date,
                    "region_id": region["id"],
                    "accuracy_score": 0.75 + random.random() * 0.2,
                    "true_positives": random.randint(5, 20),
                    "false_positives": random.randint(1, 5),
                    "true_negatives": random.randint(50, 100),
                    "false_negatives": random.randint(1, 5),
                }
            )


@router.get("/disruptions/timeline", response_model=Envelope)
async def get_disruption_timeline(
    time_range: TimeRange = Query(default="30d"),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> Envelope:
    """Get disruption timeline data for line chart."""
    _generate_mock_data()

    days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
    cutoff = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered = [d for d in _disruption_store if d["date"] >= cutoff]

    if start_date:
        filtered = [d for d in filtered if d["date"] >= start_date]
    if end_date:
        filtered = [d for d in filtered if d["date"] <= end_date]

    timeline = [DisruptionTimelinePoint.model_validate(d) for d in filtered]

    return Envelope(
        data=[t.model_dump() for t in timeline],
        error=None,
        meta=EnvelopeMeta(total=len(timeline), limit=len(timeline), offset=0),
    )


@router.get("/severity/distribution", response_model=Envelope)
async def get_severity_distribution(
    time_range: TimeRange = Query(default="30d"),
) -> Envelope:
    """Get severity distribution for donut chart."""
    _generate_mock_data()

    days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
    cutoff = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered = [d for d in _disruption_store if d["date"] >= cutoff]

    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for d in filtered:
        sev = d.get("severity", "LOW")
        severity_counts[sev] = severity_counts.get(sev, 0) + d.get("count", 1)

    total = sum(severity_counts.values())
    distribution = [
        SeverityDistribution(
            severity=sev,
            count=count,
            percentage=round(count / total * 100, 1) if total > 0 else 0,
        )
        for sev, count in severity_counts.items()
    ]

    return Envelope(data=[d.model_dump() for d in distribution], error=None, meta=None)


@router.get("/regions/metrics", response_model=Envelope)
async def get_region_metrics(
    time_range: TimeRange = Query(default="30d"),
) -> Envelope:
    """Get metrics per region for bar chart."""
    _generate_mock_data()

    regions = [
        {"id": "se_asia", "name": "Southeast Asia"},
        {"id": "europe", "name": "Europe"},
        {"id": "gulf_suez", "name": "Gulf/Suez"},
        {"id": "north_america", "name": "North America"},
        {"id": "china_ea", "name": "China/East Asia"},
    ]

    import random

    metrics = []
    for region in regions:
        metrics.append(
            RegionMetric(
                region_id=region["id"],
                region_name=region["name"],
                disruption_count=random.randint(10, 50),
                mean_time_to_detection_hours=round(random.uniform(1.5, 8.0), 1),
                auto_act_count=random.randint(2, 10),
                recommend_count=random.randint(5, 20),
                monitor_count=random.randint(10, 30),
                accuracy_score=round(random.uniform(0.75, 0.95), 2),
            )
        )

    return Envelope(data=[m.model_dump() for m in metrics], error=None, meta=None)


@router.get("/accuracy/timeline", response_model=Envelope)
async def get_accuracy_timeline(
    time_range: TimeRange = Query(default="30d"),
) -> Envelope:
    """Get accuracy scores over time for line chart."""
    _generate_mock_data()

    days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
    cutoff = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered = [a for a in _accuracy_store if a["date"] >= cutoff]

    timeline = [AccuracyTimelinePoint.model_validate(a) for a in filtered]

    return Envelope(
        data=[t.model_dump() for t in timeline],
        error=None,
        meta=EnvelopeMeta(total=len(timeline), limit=len(timeline), offset=0),
    )


@router.get("/summary", response_model=Envelope)
async def get_analytics_summary(
    time_range: TimeRange = Query(default="30d"),
) -> Envelope:
    """Get analytics summary statistics."""
    _generate_mock_data()

    days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
    cutoff = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")

    import random

    total_disruptions = sum(
        d.get("count", 1) for d in _disruption_store if d["date"] >= cutoff
    )

    decisions = [d for d in _decision_store if d["timestamp"] >= cutoff]
    auto_act = len([d for d in decisions if d["decision_type"] == "auto_act"])
    recommend = len([d for d in decisions if d["decision_type"] == "recommend"])
    monitor = len([d for d in decisions if d["decision_type"] == "monitor"])

    correct = len([d for d in decisions if d.get("correct", False)])
    accuracy = correct / len(decisions) if decisions else 0.85

    summary = AnalyticsSummary(
        total_disruptions=total_disruptions,
        total_regions=5,
        overall_accuracy=round(accuracy, 2),
        avg_time_to_detection_hours=round(random.uniform(2.5, 6.0), 1),
        decision_breakdown=DecisionBreakdown(
            auto_act=auto_act,
            recommend=recommend,
            monitor=monitor,
            total=len(decisions),
        ),
    )

    return Envelope(data=summary.model_dump(), error=None, meta=None)
