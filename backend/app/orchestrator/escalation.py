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
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EscalationDecision(BaseModel):
    """Escalation policy result for a route recommendation."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    level: str
    threshold_used: float
    action: str
    created_at: datetime


class EscalationEngine:
    """Evaluate confidence thresholds and map outputs to action channels."""

    DEFAULT_THRESHOLDS = {
        "AUTO_ACT": 0.85,
        "RECOMMEND": 0.60,
    }

    REGION_AUTO_ACT_OVERRIDE = {
        "gulf_suez": 0.90,
    }

    def evaluate(self, *, region_id: str, confidence: float, payload: dict[str, Any]) -> EscalationDecision:
        """Return escalation decision with per-region confidence tuning."""
        auto_act_threshold = self.REGION_AUTO_ACT_OVERRIDE.get(region_id, self.DEFAULT_THRESHOLDS["AUTO_ACT"])
        recommend_threshold = self.DEFAULT_THRESHOLDS["RECOMMEND"]

        if confidence >= auto_act_threshold:
            return EscalationDecision(
                region_id=region_id,
                confidence=confidence,
                level="AUTO_ACT",
                threshold_used=auto_act_threshold,
                action="trigger_tms_webhook",
                created_at=datetime.now(UTC),
            )

        if confidence >= recommend_threshold:
            return EscalationDecision(
                region_id=region_id,
                confidence=confidence,
                level="RECOMMEND",
                threshold_used=recommend_threshold,
                action="send_slack_and_email",
                created_at=datetime.now(UTC),
            )

        return EscalationDecision(
            region_id=region_id,
            confidence=confidence,
            level="MONITOR",
            threshold_used=recommend_threshold,
            action="monitor_only",
            created_at=datetime.now(UTC),
        )
