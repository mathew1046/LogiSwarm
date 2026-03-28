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

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.orchestrator.propagation_model import (
    DisruptionPropagationModel,
    PropagationResult,
    Severity,
    TradeEdge,
)


class Scenario(BaseModel):
    """A what-if disruption scenario for planning and analysis."""

    model_config = ConfigDict(extra="allow")

    scenario_id: str
    name: str
    trigger_region: str
    severity: Severity
    affected_routes: list[str] = Field(default_factory=list)
    duration_days: float = Field(ge=0.5, le=365)
    created_at: datetime
    propagation_result: PropagationResult | None = None
    mitigation_strategy: str | None = None
    mitigation_reroute_percentage: float | None = None
    mitigation_result: PropagationResult | None = None


class ScenarioCreate(BaseModel):
    """Request body for creating a new scenario."""

    name: str = Field(min_length=3, max_length=200)
    trigger_region: str = Field(min_length=1)
    severity: Severity
    affected_routes: list[str] = Field(default_factory=list)
    duration_days: float = Field(default=1.0, ge=0.5, le=365)


class ScenarioMitigation(BaseModel):
    """Request body for adding mitigation to a scenario."""

    mitigation_strategy: str = Field(min_length=3, max_length=500)
    reroute_percentage: float = Field(default=0.3, ge=0.0, le=1.0)


class ScenarioComparison(BaseModel):
    """Comparison between current impact and mitigated impact."""

    model_config = ConfigDict(extra="allow")

    scenario_id: str
    current_impact: PropagationResult
    mitigated_impact: PropagationResult | None
    improvement: dict[str, Any]
    recommendations: list[str]


class ScenarioStore:
    """In-memory storage for scenarios (can be replaced with DB persistence)."""

    def __init__(self) -> None:
        self._scenarios: dict[str, Scenario] = {}

    def save(self, scenario: Scenario) -> Scenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    def get(self, scenario_id: str) -> Scenario | None:
        return self._scenarios.get(scenario_id)

    def list(self, limit: int = 50, offset: int = 0) -> list[Scenario]:
        scenarios = sorted(
            self._scenarios.values(),
            key=lambda s: s.created_at,
            reverse=True,
        )
        return scenarios[offset : offset + limit]

    def delete(self, scenario_id: str) -> bool:
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            return True
        return False


scenario_store = ScenarioStore()


class ScenarioBuilder:
    """Build and analyze what-if disruption scenarios."""

    def __init__(self, edges: list[TradeEdge] | None = None) -> None:
        self.propagation_model = DisruptionPropagationModel(edges=edges)

    def create_scenario(self, request: ScenarioCreate) -> Scenario:
        """Create a new scenario and compute its propagation impact."""
        propagation_result = self.propagation_model.propagate(
            trigger_region=request.trigger_region,
            severity=request.severity,
            max_hops=2,
        )

        scenario = Scenario(
            scenario_id=str(uuid.uuid4()),
            name=request.name,
            trigger_region=request.trigger_region,
            severity=request.severity,
            affected_routes=request.affected_routes,
            duration_days=request.duration_days,
            created_at=datetime.now(UTC),
            propagation_result=propagation_result,
        )

        return scenario_store.save(scenario)

    def add_mitigation(
        self, scenario_id: str, mitigation: ScenarioMitigation
    ) -> Scenario | None:
        """Add mitigation strategy and compute mitigated impact."""
        scenario = scenario_store.get(scenario_id)
        if scenario is None:
            return None

        scenario.mitigation_strategy = mitigation.mitigation_strategy
        scenario.mitigation_reroute_percentage = mitigation.reroute_percentage

        severity_reduction = self._compute_severity_reduction(
            scenario.severity, mitigation.reroute_percentage
        )
        mitigated_severity = self._reduce_severity(
            scenario.severity, severity_reduction
        )

        scenario.mitigation_result = self.propagation_model.propagate(
            trigger_region=scenario.trigger_region,
            severity=mitigated_severity,
            max_hops=2,
        )

        return scenario_store.save(scenario)

    def compare_impact(self, scenario_id: str) -> ScenarioComparison | None:
        """Compare current impact with mitigated impact for a scenario."""
        scenario = scenario_store.get(scenario_id)
        if scenario is None or scenario.propagation_result is None:
            return None

        current = scenario.propagation_result
        mitigated = scenario.mitigation_result

        recommendations = self._generate_recommendations(scenario)

        improvement: dict[str, Any] = {}
        if mitigated:
            improvement = {
                "regions_affected_reduction": len(current.affected_regions)
                - len(mitigated.affected_regions),
                "delay_hours_reduction": round(
                    current.estimated_delay_propagation_hours
                    - mitigated.estimated_delay_propagation_hours,
                    2,
                ),
                "cascade_score_reduction": round(
                    sum(n.cascade_score for n in current.affected_regions)
                    - sum(n.cascade_score for n in mitigated.affected_regions),
                    4,
                ),
                "mitigation_effectiveness": scenario.mitigation_reroute_percentage
                if scenario.mitigation_reroute_percentage
                else 0.0,
            }

        return ScenarioComparison(
            scenario_id=scenario_id,
            current_impact=current,
            mitigated_impact=mitigated,
            improvement=improvement,
            recommendations=recommendations,
        )

    def _compute_severity_reduction(
        self, severity: Severity, reroute_percentage: float
    ) -> float:
        """Compute severity reduction factor based on reroute percentage."""
        base_reduction = reroute_percentage * 0.5
        severity_multipliers = {"LOW": 0.5, "MEDIUM": 0.3, "HIGH": 0.2, "CRITICAL": 0.1}
        return base_reduction * severity_multipliers.get(severity, 0.3)

    def _reduce_severity(self, severity: Severity, reduction: float) -> Severity:
        """Reduce severity level based on reduction factor."""
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        current_idx = severity_order.index(severity)
        steps = int(reduction * 3)
        new_idx = min(current_idx + steps, len(severity_order) - 1)
        return severity_order[new_idx]  # type: ignore[return-value]

    def _generate_recommendations(self, scenario: Scenario) -> list[str]:
        """Generate actionable recommendations for the scenario."""
        recommendations = []

        if scenario.severity in ("HIGH", "CRITICAL"):
            recommendations.append(
                f"Prioritize {scenario.trigger_region} monitoring. "
                f"Consider activating backup suppliers/routes immediately."
            )

        if scenario.propagation_result:
            if len(scenario.propagation_result.affected_regions) > 2:
                recommendations.append(
                    "Multi-region cascade risk detected. "
                    "Coordinate with downstream partners proactively."
                )

            for region in scenario.propagation_result.affected_regions[:3]:
                if region.delay_hours > 48:
                    recommendations.append(
                        f"{region.region_id}: Estimated delay {region.delay_hours:.0f}h. "
                        f"Consider inventory buffer adjustments."
                    )

        if scenario.mitigation_strategy:
            recommendations.append(f"Mitigation: {scenario.mitigation_strategy}")

        if not recommendations:
            recommendations.append("Monitor situation. No immediate action required.")

        return recommendations
