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

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class InventoryBufferRecommendation(BaseModel):
    """Single destination/product category inventory buffer recommendation."""

    model_config = ConfigDict(extra="allow")

    destination_region: str
    product_category: str = "general"
    current_buffer_days: float = Field(ge=0.0)
    recommended_buffer_days: float = Field(ge=0.0)
    buffer_increase_percent: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class InventoryAdvisorResult(BaseModel):
    """Full inventory buffer recommendation output."""

    model_config = ConfigDict(extra="allow")

    disruption_id: str
    trigger_region: str
    severity: Severity
    estimated_duration_days: float
    affected_destinations: list[InventoryBufferRecommendation]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InventoryAdvisor:
    """Compute inventory buffer increase recommendations based on disruption severity and duration."""

    SEVERITY_MULTIPLIERS: dict[Severity, float] = {
        "LOW": 0.3,
        "MEDIUM": 0.6,
        "HIGH": 1.2,
        "CRITICAL": 2.0,
    }

    CATEGORY_ADJUSTMENTS: dict[str, float] = {
        "perishable": 0.5,
        "electronics": 1.3,
        "pharmaceuticals": 1.5,
        "automotive": 1.1,
        "consumer_goods": 1.0,
        "raw_materials": 0.9,
        "machinery": 1.2,
        "general": 1.0,
    }

    UNCERTAINTY_FACTOR = 0.15

    DEFAULT_REGION_DEPENDENCIES: dict[str, list[str]] = {
        "se_asia": ["china_ea", "north_america"],
        "europe": ["north_america", "china_ea"],
        "gulf_suez": ["europe", "se_asia"],
        "north_america": ["europe", "china_ea"],
        "china_ea": ["se_asia", "north_america"],
    }

    def __init__(
        self,
        region_dependencies: dict[str, list[str]] | None = None,
    ) -> None:
        self.region_dependencies = (
            region_dependencies or self.DEFAULT_REGION_DEPENDENCIES
        )

    def recommend(
        self,
        disruption_id: str,
        trigger_region: str,
        severity: Severity,
        estimated_duration_days: float,
        affected_product_categories: list[str] | None = None,
        destination_regions: list[str] | None = None,
        current_buffers: dict[str, float] | None = None,
    ) -> InventoryAdvisorResult:
        severity_key = severity.upper()
        severity_multiplier = self.SEVERITY_MULTIPLIERS.get(severity_key, 1.0)
        categories = affected_product_categories or ["general"]
        destinations = destination_regions or self._get_downstream_regions(
            trigger_region
        )
        current_buffers = current_buffers or {}

        recommendations: list[InventoryBufferRecommendation] = []
        for dest_region in destinations:
            current_buffer = current_buffers.get(dest_region, 7.0)

            for category in categories:
                category_adj = self.CATEGORY_ADJUSTMENTS.get(category, 1.0)
                buffer_days = (
                    severity_multiplier
                    * estimated_duration_days
                    * (1 + self.UNCERTAINTY_FACTOR)
                    * category_adj
                )

                buffer_increase_percent = (
                    (current_buffer + buffer_days) / max(current_buffer, 1.0) - 1.0
                ) * 100

                confidence = self._calculate_confidence(
                    severity=severity_key,
                    duration=estimated_duration_days,
                )

                reasoning = self._build_reasoning(
                    trigger_region=trigger_region,
                    dest_region=dest_region,
                    severity=severity_key,
                    buffer_days=buffer_days,
                    category=category,
                )

                recommendations.append(
                    InventoryBufferRecommendation(
                        destination_region=dest_region,
                        product_category=category,
                        current_buffer_days=current_buffer,
                        recommended_buffer_days=round(current_buffer + buffer_days, 1),
                        buffer_increase_percent=round(buffer_increase_percent, 1),
                        confidence=confidence,
                        reasoning=reasoning,
                    )
                )

        return InventoryAdvisorResult(
            disruption_id=disruption_id,
            trigger_region=trigger_region,
            severity=severity_key,
            estimated_duration_days=estimated_duration_days,
            affected_destinations=recommendations,
        )

    def _get_downstream_regions(self, trigger_region: str) -> list[str]:
        return self.region_dependencies.get(trigger_region, [])

    def _calculate_confidence(self, severity: Severity, duration: float) -> float:
        base_confidence = {
            "LOW": 0.9,
            "MEDIUM": 0.8,
            "HIGH": 0.7,
            "CRITICAL": 0.65,
        }.get(severity, 0.7)

        duration_penalty = min(duration / 30.0, 0.2)

        return round(max(base_confidence - duration_penalty, 0.5), 2)

    def _build_reasoning(
        self,
        trigger_region: str,
        dest_region: str,
        severity: Severity,
        buffer_days: float,
        category: str,
    ) -> str:
        severity_text = {
            "LOW": "minor",
            "MEDIUM": "moderate",
            "HIGH": "significant",
            "CRITICAL": "severe",
        }.get(severity, "moderate")

        return (
            f"{severity_text.capitalize()} disruption in {trigger_region} affects downstream "
            f"destinations including {dest_region}. Recommend adding {buffer_days:.1f} days of "
            f"{category} inventory buffer to maintain service levels during disruption period."
        )


inventory_advisor = InventoryAdvisor()
