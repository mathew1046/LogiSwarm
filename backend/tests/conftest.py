from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.agents.base_agent import Event
from app.orchestrator.propagation_model import PropagationResult, PropagationNode


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    client = MagicMock()
    client.api_key = "test-api-key"

    async def mock_reason(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "severity": "HIGH",
            "confidence": 0.85,
            "reasoning": "Test reasoning from mock LLM",
            "recommended_actions": [
                "Monitor situation closely",
                "Activate backup suppliers",
            ],
            "affected_routes": ["route_1", "route_2"],
        }

    client.reason = mock_reason
    return client


@pytest.fixture
def mock_zep_client():
    """Create a mock Zep memory client for testing."""
    client = MagicMock()

    async def mock_search_similar_episodes(
        region_id: str, anomaly_description: str, top_k: int = 3
    ) -> list[dict[str, Any]]:
        return []

    client.search_similar_episodes = mock_search_similar_episodes
    return client


@pytest.fixture
def mock_events():
    """Create a list of mock events for testing."""
    now = datetime.now(UTC)
    return [
        Event(
            source="ais",
            event_type="VESSEL_CONGESTION",
            severity="HIGH",
            lat=25.0,
            lon=55.0,
            timestamp=now,
            raw={"vessel_count": 150},
        ),
        Event(
            source="weather",
            event_type="STORM_WARNING",
            severity="MEDIUM",
            lat=24.5,
            lon=54.5,
            timestamp=now,
            raw={"wind_speed": 45},
        ),
        Event(
            source="port_simulator",
            event_type="CRANE_IDLE",
            severity="LOW",
            lat=25.1,
            lon=55.1,
            timestamp=now,
            raw={"idle_hours": 6},
        ),
    ]


@pytest.fixture
def sample_propagation_result():
    """Create a sample propagation result for testing."""
    return PropagationResult(
        trigger_region="gulf_suez",
        severity="HIGH",
        affected_regions=[
            PropagationNode(
                region_id="europe",
                hops=1,
                path=["gulf_suez", "europe"],
                delay_hours=12.0,
                cascade_score=0.85,
            ),
            PropagationNode(
                region_id="se_asia",
                hops=2,
                path=["gulf_suez", "europe", "se_asia"],
                delay_hours=24.0,
                cascade_score=0.65,
            ),
        ],
        estimated_delay_propagation_hours=36.0,
        cascade_timeline=[
            {
                "region_id": "europe",
                "eta_hours": 12.0,
                "hops": 1,
                "cascade_score": 0.85,
            },
            {
                "region_id": "se_asia",
                "eta_hours": 24.0,
                "hops": 2,
                "cascade_score": 0.65,
            },
        ],
        generated_at=datetime.now(UTC),
    )


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
