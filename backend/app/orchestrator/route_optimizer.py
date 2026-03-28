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
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.orchestrator.multimodal_graph import (
    MULTIMODAL_GRAPH,
    MULTIMODAL_NODES,
    TransportMode,
)


class RouteAlternative(BaseModel):
    """Single alternative route candidate scored by cost/time/reliability."""

    model_config = ConfigDict(extra="allow")

    route_id: str
    path: list[str]
    modes: list[str] = Field(default_factory=lambda: ["sea"])
    score: float
    cost_delta: float
    eta_delta_hours: float
    reliability: float
    multimodal: bool = False


class RouteOptimizationResult(BaseModel):
    """Top route alternatives plus optional LLM summary for operations."""

    model_config = ConfigDict(extra="allow")

    origin: str
    destination: str
    disrupted_regions: list[str]
    alternatives: list[RouteAlternative]
    summary: str
    generated_at: datetime
    multimodal_available: bool = False


class RouteOptimizationEngine:
    """Compute top-3 route alternatives using a disruption-aware weighted graph with multi-modal support."""

    def __init__(
        self, llm_client: object | None = None, use_multimodal: bool = True
    ) -> None:
        self.llm_client = llm_client
        self.use_multimodal = use_multimodal
        self.graph = self._default_route_graph()
        self.multimodal_graph = MULTIMODAL_GRAPH if use_multimodal else {}

async def optimize(
        self,
        *,
        origin: str,
        destination: str,
        current_route: list[str],
        disrupted_regions: list[str],
    ) -> RouteOptimizationResult:
        """Return top-3 alternatives excluding disrupted regions where possible."""
        blocked = {region for region in disrupted_regions}
        
        alternatives = self._k_shortest_paths(origin=origin, destination=destination, blocked=blocked, k=3)
        
        multimodal_alternatives = []
        if self.use_multimodal:
            multimodal_alternatives = self._find_multimodal_paths(
                origin=origin, destination=destination, blocked=blocked, k=2
            )
        
        all_alternatives = alternatives + multimodal_alternatives
        all_alternatives.sort(key=lambda x: x.score)
        all_alternatives = all_alternatives[:5]
        
        result = RouteOptimizationResult(
            origin=origin,
            destination=destination,
            disrupted_regions=disrupted_regions,
            alternatives=all_alternatives,
            summary="",
            generated_at=datetime.now(UTC),
            multimodal_available=len(multimodal_alternatives) > 0,
        )
        result.summary = await self._summarize_with_llm(current_route=current_route, result=result)
        return result

    def _k_shortest_paths(
        self, *, origin: str, destination: str, blocked: set[str], k: int
    ) -> list[RouteAlternative]:
        candidates: list[RouteAlternative] = []

        # Multi-path best-first search with path-state to approximate top-k candidates.
        queue: list[tuple[float, str, list[str], float, float, float]] = [
            (0.0, origin, [origin], 0.0, 0.0, 1.0)
        ]

        while queue and len(candidates) < k:
            score, node, path, cost_delta, eta_delta, reliability = heapq.heappop(queue)
            if node == destination:
                candidates.append(
                    RouteAlternative(
                        route_id=f"alt-{len(candidates) + 1}",
                        path=path,
                        score=round(score, 4),
                        cost_delta=round(cost_delta, 2),
                        eta_delta_hours=round(eta_delta, 2),
                        reliability=round(reliability, 3),
                    )
                )
                continue

            for edge in self.graph.get(node, []):
                target = edge["target"]
                if target in path:
                    continue
                if target in blocked and target != destination:
                    continue

                next_path = [*path, target]
                next_cost = cost_delta + edge["cost"]
                next_eta = eta_delta + edge["time"]
                next_reliability = reliability * edge["reliability"]

                weighted_score = next_cost + next_eta + ((1 - next_reliability) * 10)
                heapq.heappush(
                    queue,
                    (
                        weighted_score,
                        target,
                        next_path,
                        next_cost,
                        next_eta,
                        next_reliability,
                    ),
                )

        return candidates

    def _find_multimodal_paths(
        self, *, origin: str, destination: str, blocked: set[str], k: int
    ) -> list[RouteAlternative]:
        if origin not in MULTIMODAL_NODES or destination not in MULTIMODAL_NODES:
            return []
        
        candidates: list[RouteAlternative] = []
        queue: list[tuple[float, str, list[str], list[str], float, float, float]] = [
            (0.0, origin, [origin], [], 0.0, 0.0, 1.0)
        ]
        
        while queue and len(candidates) < k:
            score, node, path, modes, cost_delta, eta_delta, reliability = heapq.heappop(queue)
            
            if node == destination:
                candidates.append(
                    RouteAlternative(
                        route_id=f"multimodal-{len(candidates) + 1}",
                        path=path,
                        modes=[m.value for m in modes] if modes else ["sea"],
                        score=round(score, 4),
                        cost_delta=round(cost_delta, 2),
                        eta_delta_hours=round(eta_delta, 2),
                        reliability=round(reliability, 3),
                        multimodal=len(set(modes)) > 1 if modes else False,
                    )
                )
                continue
            
            for edge in self.multimodal_graph.get(node, []):
                target = edge["target"]
                if target in path:
                    continue
                if target in blocked and target != destination:
                    continue
                
                mode = edge.get("mode", TransportMode.SEA)
                next_path = [*path, target]
                next_modes = modes + [mode]
                next_cost = cost_delta + edge["cost"]
                next_eta = eta_delta + edge["time"]
                next_reliability = reliability * edge["reliability"]
                
                weighted_score = next_cost + next_eta + ((1 - next_reliability) * 10)
                heapq.heappush(
                    queue,
                    (weighted_score, target, next_path, next_modes, next_cost, next_eta, next_reliability),
                )
        
        return candidates

    async def _summarize_with_llm(
        self, *, current_route: list[str], result: RouteOptimizationResult
    ) -> str:
        if not self.llm_client or not hasattr(self.llm_client, "reason"):
            return self._fallback_summary(current_route=current_route, result=result)

        payload = {
            "region_id": "orchestrator",
            "region_name": "global",
            "system_prompt": (
                "You summarize route alternatives for logistics operations in concise plain English. "
                "Highlight tradeoffs in time, cost, and reliability."
            ),
            "events": [
                {
                    "current_route": current_route,
                    "alternatives": [
                        alt.model_dump(mode="json") for alt in result.alternatives
                    ],
                    "disrupted_regions": result.disrupted_regions,
                }
            ],
            "memory_episodes": [],
        }

        try:
            decision = await self.llm_client.reason(payload)
            reasoning = (
                decision.get("reasoning") if isinstance(decision, dict) else None
            )
            if isinstance(reasoning, str) and reasoning.strip():
                return reasoning.strip()
        except Exception:
            pass

        return self._fallback_summary(current_route=current_route, result=result)

    @staticmethod
    def _fallback_summary(
        *, current_route: list[str], result: RouteOptimizationResult
    ) -> str:
        if not result.alternatives:
            return "No clean alternative route found; keep monitoring and escalate to manual planning."

        best = result.alternatives[0]
        return (
            f"Current route {' → '.join(current_route)} intersects disrupted regions. "
            f"Best alternative is {' → '.join(best.path)} with cost delta {best.cost_delta:+.2f}, "
            f"ETA delta {best.eta_delta_hours:+.2f}h, reliability {best.reliability:.2f}."
        )

    @staticmethod
    def _default_route_graph() -> dict[str, list[dict[str, Any]]]:
        return {
            "china_ea": [
                {"target": "se_asia", "cost": 1.4, "time": 20.0, "reliability": 0.92},
                {
                    "target": "north_america",
                    "cost": 2.8,
                    "time": 28.0,
                    "reliability": 0.84,
                },
            ],
            "se_asia": [
                {"target": "gulf_suez", "cost": 1.2, "time": 18.0, "reliability": 0.9},
                {
                    "target": "north_america",
                    "cost": 3.3,
                    "time": 30.0,
                    "reliability": 0.82,
                },
            ],
            "gulf_suez": [
                {"target": "europe", "cost": 1.1, "time": 14.0, "reliability": 0.91},
                {
                    "target": "north_america",
                    "cost": 2.6,
                    "time": 23.0,
                    "reliability": 0.8,
                },
            ],
            "europe": [
                {
                    "target": "north_america",
                    "cost": 1.7,
                    "time": 12.0,
                    "reliability": 0.89,
                },
                {"target": "gulf_suez", "cost": 1.3, "time": 15.0, "reliability": 0.86},
            ],
            "north_america": [
                {"target": "europe", "cost": 1.9, "time": 13.0, "reliability": 0.88},
            ],
        }
