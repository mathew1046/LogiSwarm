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
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import UTC, datetime

from app.agents.base_agent import GeoAgent, Event, PerceptionResult


class MockGeoAgent(GeoAgent):
    """Concrete implementation of GeoAgent for testing."""

    REGION_ID = "test_region"
    REGION_NAME = "Test Region"
    BBOX = (-10.0, -10.0, 10.0, 10.0)

    def get_system_prompt(self) -> str:
        return "You are a test geo-agent."


@pytest.fixture
def test_agent(mock_llm_client, mock_zep_client):
    """Create a test agent instance."""
    return MockGeoAgent(
        region_id="test_region",
        region_name="Test Region",
        bbox=(-10.0, -10.0, 10.0, 10.0),
        llm_client=mock_llm_client,
        zep_client=mock_zep_client,
    )


class TestGeoAgentLifecycle:
    """Test the agent perceive-reason-act lifecycle."""

    @pytest.mark.asyncio
    async def test_perceive_returns_events(self, test_agent, mock_events):
        """Test that perceive returns events from aggregator."""
        mock_aggregator = MagicMock()
        mock_aggregator.get_region_events = AsyncMock(return_value=(mock_events, False))
        test_agent.aggregator = mock_aggregator

        result = await test_agent.perceive()

        assert isinstance(result, PerceptionResult)
        assert len(result.events) == 3
        assert result.is_degraded is False

    @pytest.mark.asyncio
    async def test_perceive_handles_degraded_mode(self, test_agent, mock_events):
        """Test that perceive handles degraded mode correctly."""
        mock_aggregator = MagicMock()
        mock_aggregator.get_region_events = AsyncMock(return_value=(mock_events, True))
        mock_aggregator.get_degradation_status = AsyncMock()
        mock_aggregator.get_degradation_status.return_value = MagicMock(
            mode="DEGRADED",
            degraded_connectors=["weather"],
            uncertainty_factor=0.25,
        )
        test_agent.aggregator = mock_aggregator

        result = await test_agent.perceive()

        assert result.is_degraded is True
        assert test_agent.last_degradation_status is not None

    @pytest.mark.asyncio
    async def test_reason_returns_decision(self, test_agent, mock_events):
        """Test that reason returns a structured decision."""
        mock_aggregator = MagicMock()
        mock_aggregator.get_region_events = AsyncMock(return_value=(mock_events, False))
        test_agent.aggregator = mock_aggregator

        result = await test_agent.perceive()
        decision = await test_agent.reason(result.events, result)

        assert "severity" in decision
        assert "confidence" in decision
        assert "reasoning" in decision
        assert "recommended_actions" in decision
        assert decision["region_id"] == "test_region"

    @pytest.mark.asyncio
    async def test_reason_adds_uncertainty_in_degraded_mode(
        self, test_agent, mock_events
    ):
        """Test that confidence is reduced in degraded mode."""
        mock_aggregator = MagicMock()
        mock_aggregator.get_region_events = AsyncMock(return_value=(mock_events, True))
        mock_aggregator.get_degradation_status = AsyncMock()
        mock_aggregator.get_degradation_status.return_value = MagicMock(
            mode="OFFLINE",
            degraded_connectors=["ais", "weather"],
            uncertainty_factor=0.5,
            cached_data_age_minutes=120.0,
        )
        test_agent.aggregator = mock_aggregator

        result = await test_agent.perceive()
        decision = await test_agent.reason(result.events, result)

        assert decision.get("is_degraded") is True
        assert "UNCERTAINTY WARNING" in decision.get("reasoning", "")


class TestGeoAgentBroadcast:
    """Test inter-agent broadcast functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_to_neighbors(self, test_agent):
        """Test that agent broadcasts to neighbors correctly."""
        test_agent.set_neighbors(["region_1", "region_2"])

        with patch(
            "app.agents.base_agent.publish", new_callable=AsyncMock
        ) as mock_publish:
            mock_publish.return_value = 1

            event = {
                "severity": "HIGH",
                "reasoning": "Test broadcast",
                "region_id": "test_region",
            }
            await test_agent.broadcast_to_neighbors(event)

            assert mock_publish.call_count == 2

    @pytest.mark.asyncio
    async def test_no_broadcast_for_low_severity(self, test_agent):
        """Test that low severity events are not broadcast."""
        test_agent.set_neighbors(["region_1"])

        with patch(
            "app.agents.base_agent.publish", new_callable=AsyncMock
        ) as mock_publish:
            decision = {
                "severity": "LOW",
                "reasoning": "Test decision",
            }
            await test_agent.act(decision)

            mock_publish.assert_called_once()


class TestGeoAgentInterview:
    """Test agent interview functionality."""

    @pytest.mark.asyncio
    async def test_interview_returns_answer(self, test_agent):
        """Test that interview returns a structured answer."""
        result = await test_agent.interview("What are the current risk factors?")

        assert "region_id" in result
        assert "question" in result
        assert "answer" in result
        assert "sources" in result
        assert result["region_id"] == "test_region"

    @pytest.mark.asyncio
    async def test_interview_uses_memory_search(self, test_agent, mock_zep_client):
        """Test that interview searches memory for relevant episodes."""
        await test_agent.interview("What historical disruptions occurred?")

        mock_zep_client.search_similar_episodes.assert_called_once()
