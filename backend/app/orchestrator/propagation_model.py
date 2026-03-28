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

import heapq
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class TradeEdge(BaseModel):
    """Directed dependency edge between two logistics regions."""

    model_config = ConfigDict(extra="allow")

    source: str
    target: str
    volume_weight: float = Field(ge=0.0)
    dependency_score: float = Field(ge=0.0)


class PropagationNode(BaseModel):
    """Projected disruption impact for a downstream region."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    hops: int = Field(ge=1)
    path: list[str]
    delay_hours: float = Field(ge=0.0)
    cascade_score: float = Field(ge=0.0)


class PropagationResult(BaseModel):
    """Output of disruption propagation scoring across regional trade graph."""

    model_config = ConfigDict(extra="allow")

    trigger_region: str
    severity: Severity
    affected_regions: list[PropagationNode]
    estimated_delay_propagation_hours: float = Field(ge=0.0)
    cascade_timeline: list[dict[str, str | int | float]]
    generated_at: datetime


class DisruptionPropagationModel:
    """Compute downstream disruption cascade with weighted region graph traversal."""

    _SEVERITY_MULTIPLIER = {
        "LOW": 0.5,
        "MEDIUM": 1.0,
        "HIGH": 1.7,
        "CRITICAL": 2.4,
    }

    def __init__(self, edges: list[TradeEdge] | None = None) -> None:
        self.edges = edges or self._default_edges()
        self._adjacency: dict[str, list[TradeEdge]] = {}
        for edge in self.edges:
            self._adjacency.setdefault(edge.source, []).append(edge)

    def propagate(
        self,
        trigger_region: str,
        severity: Severity,
        max_hops: int = 2,
    ) -> PropagationResult:
        """Run weighted graph traversal and score disruption cascade impact."""
        severity_key = severity.upper()
        severity_multiplier = self._SEVERITY_MULTIPLIER.get(severity_key, 1.0)

        queue: list[tuple[float, int, str, list[str]]] = [(0.0, 0, trigger_region, [trigger_region])]
        best_cost_by_region: dict[str, float] = {trigger_region: 0.0}
        impacted: dict[str, PropagationNode] = {}

        while queue:
            cost, hops, region, path = heapq.heappop(queue)
            if hops >= max_hops:
                continue

            for edge in self._adjacency.get(region, []):
                next_hops = hops + 1
                lane_weight = edge.volume_weight * edge.dependency_score
                time_decay = self._time_decay(next_hops)
                cascade_score = severity_multiplier * lane_weight * time_decay
                next_cost = cost + (1.0 / max(cascade_score, 1e-6))

                if edge.target in best_cost_by_region and next_cost >= best_cost_by_region[edge.target]:
                    continue

                best_cost_by_region[edge.target] = next_cost
                next_path = [*path, edge.target]
                delay_hours = round(4.0 * next_hops * severity_multiplier * lane_weight, 2)

                impacted[edge.target] = PropagationNode(
                    region_id=edge.target,
                    hops=next_hops,
                    path=next_path,
                    delay_hours=delay_hours,
                    cascade_score=round(cascade_score, 4),
                )
                heapq.heappush(queue, (next_cost, next_hops, edge.target, next_path))

        affected_regions = sorted(
            impacted.values(),
            key=lambda item: (item.hops, -item.cascade_score),
        )
        timeline = [
            {
                "region_id": node.region_id,
                "eta_hours": node.delay_hours,
                "hops": node.hops,
                "cascade_score": node.cascade_score,
            }
            for node in affected_regions
        ]

        return PropagationResult(
            trigger_region=trigger_region,
            severity=severity_key,  # type: ignore[arg-type]
            affected_regions=affected_regions,
            estimated_delay_propagation_hours=round(sum(node.delay_hours for node in affected_regions), 2),
            cascade_timeline=timeline,
            generated_at=datetime.now(UTC),
        )

    @staticmethod
    def _time_decay(hops: int) -> float:
        # Hop-1 keeps full strength, hop-2 attenuates, etc.
        return 1.0 / (1.0 + (hops - 1) * 0.6)

    @staticmethod
    def _default_edges() -> list[TradeEdge]:
        return [
            TradeEdge(source="se_asia", target="gulf_suez", volume_weight=0.92, dependency_score=0.9),
            TradeEdge(source="gulf_suez", target="europe", volume_weight=0.95, dependency_score=0.94),
            TradeEdge(source="europe", target="north_america", volume_weight=0.72, dependency_score=0.7),
            TradeEdge(source="china_ea", target="se_asia", volume_weight=0.85, dependency_score=0.8),
            TradeEdge(source="china_ea", target="north_america", volume_weight=0.78, dependency_score=0.74),
            TradeEdge(source="north_america", target="europe", volume_weight=0.63, dependency_score=0.62),
            TradeEdge(source="gulf_suez", target="se_asia", volume_weight=0.71, dependency_score=0.68),
        ]
