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

import pytest

from app.orchestrator.propagation_model import (
    DisruptionPropagationModel,
    PropagationResult,
    PropagationNode,
    TradeEdge,
)


class TestPropagationModel:
    """Test the disruption propagation model."""

    def test_propagate_single_hop(self):
        """Test propagation with single hop from trigger region."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="gulf_suez",
            severity="HIGH",
            max_hops=1,
        )

        assert result.trigger_region == "gulf_suez"
        assert result.severity == "HIGH"
        assert len(result.affected_regions) >= 1
        assert all(node.hops == 1 for node in result.affected_regions)

    def test_propagate_two_hops(self):
        """Test propagation with two hops from trigger region."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="se_asia",
            severity="CRITICAL",
            max_hops=2,
        )

        assert result.trigger_region == "se_asia"
        assert result.severity == "CRITICAL"
        assert len(result.affected_regions) >= 1

    def test_propagation_scores_in_order(self):
        """Test that cascade scores are ordered correctly."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="gulf_suez",
            severity="HIGH",
            max_hops=2,
        )

        if len(result.affected_regions) > 1:
            for i in range(len(result.affected_regions) - 1):
                current = result.affected_regions[i]
                next_node = result.affected_regions[i + 1]
                assert current.hops <= next_node.hops

    def test_severity_affects_cascade_score(self):
        """Test that higher severity increases cascade score."""
        model = DisruptionPropagationModel()

        low_result = model.propagate(
            trigger_region="gulf_suez",
            severity="LOW",
            max_hops=1,
        )

        critical_result = model.propagate(
            trigger_region="gulf_suez",
            severity="CRITICAL",
            max_hops=1,
        )

        if low_result.affected_regions and critical_result.affected_regions:
            low_score = low_result.affected_regions[0].cascade_score
            critical_score = critical_result.affected_regions[0].cascade_score
            assert critical_score > low_score

    def test_time_decay_reduces_impact(self):
        """Test that time decay reduces impact at higher hops."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="se_asia",
            severity="HIGH",
            max_hops=2,
        )

        hop_1_nodes = [n for n in result.affected_regions if n.hops == 1]
        hop_2_nodes = [n for n in result.affected_regions if n.hops == 2]

        if hop_1_nodes and hop_2_nodes:
            avg_hop_1 = sum(n.cascade_score for n in hop_1_nodes) / len(hop_1_nodes)
            avg_hop_2 = sum(n.cascade_score for n in hop_2_nodes) / len(hop_2_nodes)
            assert avg_hop_1 >= avg_hop_2

    def test_cascade_timeline_generated(self):
        """Test that cascade timeline is generated correctly."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="europe",
            severity="MEDIUM",
            max_hops=2,
        )

        assert len(result.cascade_timeline) == len(result.affected_regions)
        for entry in result.cascade_timeline:
            assert "region_id" in entry
            assert "eta_hours" in entry
            assert "hops" in entry

    def test_custom_edges(self):
        """Test propagation with custom trade edges."""
        custom_edges = [
            TradeEdge(
                source="region_a",
                target="region_b",
                volume_weight=0.9,
                dependency_score=0.8,
            ),
            TradeEdge(
                source="region_b",
                target="region_c",
                volume_weight=0.7,
                dependency_score=0.6,
            ),
        ]

        model = DisruptionPropagationModel(edges=custom_edges)

        result = model.propagate(
            trigger_region="region_a",
            severity="HIGH",
            max_hops=2,
        )

        assert result.trigger_region == "region_a"
        affected_ids = [n.region_id for n in result.affected_regions]
        assert "region_b" in affected_ids
        assert "region_c" in affected_ids

    def test_delay_hours_calculated(self):
        """Test that delay hours are calculated for affected regions."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="gulf_suez",
            severity="HIGH",
            max_hops=2,
        )

        for node in result.affected_regions:
            assert node.delay_hours >= 0
            assert isinstance(node.delay_hours, float)

    def test_estimated_delay_propagation_sum(self):
        """Test that estimated delay propagation is sum of all delays."""
        model = DisruptionPropagationModel()

        result = model.propagate(
            trigger_region="china_ea",
            severity="CRITICAL",
            max_hops=2,
        )

        total_delay = sum(node.delay_hours for node in result.affected_regions)
        assert result.estimated_delay_propagation_hours == pytest.approx(
            total_delay, rel=0.01
        )
