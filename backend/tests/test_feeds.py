from __future__ import annotations

import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.feeds.aggregator import FeedAggregator, Event, FeedHealth


class TestFeedAggregator:
    """Test the feed aggregator functionality."""

    @pytest.fixture
    def aggregator(self):
        """Create a feed aggregator instance."""
        return FeedAggregator()

    @pytest.mark.asyncio
    async def test_get_region_events_returns_events(self, aggregator):
        """Test that get_region_events returns events."""
        with patch.object(aggregator, "_from_ais", new_callable=AsyncMock) as mock_ais:
            with patch.object(
                aggregator, "_from_weather", new_callable=AsyncMock
            ) as mock_weather:
                with patch.object(
                    aggregator, "_from_port", new_callable=AsyncMock
                ) as mock_port:
                    with patch.object(
                        aggregator, "_from_carrier", new_callable=AsyncMock
                    ) as mock_carrier:
                        with patch.object(
                            aggregator, "_from_gdelt", new_callable=AsyncMock
                        ) as mock_gdelt:
                            mock_ais.return_value = [
                                Event(
                                    source="ais",
                                    event_type="VESSEL_POSITION",
                                    severity="LOW",
                                    lat=25.0,
                                    lon=55.0,
                                    timestamp=datetime.now(UTC),
                                    raw={},
                                )
                            ]
                            mock_weather.return_value = []
                            mock_port.return_value = []
                            mock_carrier.return_value = []
                            mock_gdelt.return_value = []

                            events, is_degraded = await aggregator.get_region_events(
                                region_id="se_asia",
                                lookback_minutes=60,
                            )

                            assert isinstance(events, list)
                            assert isinstance(is_degraded, bool)

    @pytest.mark.asyncio
    async def test_get_region_events_deduplicates(self, aggregator):
        """Test that events are deduplicated."""
        now = datetime.now(UTC)
        duplicate_event = Event(
            source="ais",
            event_type="VESSEL_POSITION",
            severity="LOW",
            lat=25.0,
            lon=55.0,
            timestamp=now,
            raw={},
        )

        with patch.object(aggregator, "_from_ais", new_callable=AsyncMock) as mock_ais:
            with patch.object(
                aggregator, "_from_weather", new_callable=AsyncMock
            ) as mock_weather:
                with patch.object(
                    aggregator, "_from_port", new_callable=AsyncMock
                ) as mock_port:
                    with patch.object(
                        aggregator, "_from_carrier", new_callable=AsyncMock
                    ) as mock_carrier:
                        with patch.object(
                            aggregator, "_from_gdelt", new_callable=AsyncMock
                        ) as mock_gdelt:
                            mock_ais.return_value = [duplicate_event, duplicate_event]
                            mock_weather.return_value = []
                            mock_port.return_value = []
                            mock_carrier.return_value = []
                            mock_gdelt.return_value = []

                            events, _ = await aggregator.get_region_events(
                                region_id="se_asia"
                            )

                            timestamps = [e.timestamp.isoformat() for e in events]
                            assert len(timestamps) == len(set(timestamps))

    @pytest.mark.asyncio
    async def test_get_connectors_health(self, aggregator):
        """Test that get_connectors_health returns health for all connectors."""
        with patch.object(aggregator, "_from_ais", new_callable=AsyncMock) as mock_ais:
            with patch.object(aggregator, "_from_weather", new_callable=AsyncMock):
                with patch.object(aggregator, "_from_port", new_callable=AsyncMock):
                    with patch.object(
                        aggregator, "_from_carrier", new_callable=AsyncMock
                    ):
                        with patch.object(
                            aggregator, "_from_gdelt", new_callable=AsyncMock
                        ):
                            mock_ais.return_value = []

                            health = await aggregator.get_connectors_health("se_asia")

                            assert isinstance(health, list)
                            assert len(health) == 5
                            connector_names = [h.connector for h in health]
                            assert "ais" in connector_names
                            assert "weather" in connector_names

    @pytest.mark.asyncio
    async def test_degraded_status_when_all_fail(self, aggregator):
        """Test that degraded status is returned when all connectors fail."""
        with patch.object(aggregator, "_from_ais", new_callable=AsyncMock) as mock_ais:
            with patch.object(
                aggregator, "_from_weather", new_callable=AsyncMock
            ) as mock_weather:
                with patch.object(
                    aggregator, "_from_port", new_callable=AsyncMock
                ) as mock_port:
                    with patch.object(
                        aggregator, "_from_carrier", new_callable=AsyncMock
                    ) as mock_carrier:
                        with patch.object(
                            aggregator, "_from_gdelt", new_callable=AsyncMock
                        ) as mock_gdelt:
                            mock_ais.side_effect = Exception("Connection failed")
                            mock_weather.side_effect = Exception("Connection failed")
                            mock_port.side_effect = Exception("Connection failed")
                            mock_carrier.side_effect = Exception("Connection failed")
                            mock_gdelt.side_effect = Exception("Connection failed")

                            events, is_degraded = await aggregator.get_region_events(
                                region_id="se_asia"
                            )

                            assert is_degraded is True
                            assert events == []

    @pytest.mark.asyncio
    async def test_get_degradation_status(self, aggregator):
        """Test that get_degradation_status returns status."""
        status = await aggregator.get_degradation_status("se_asia")

        assert hasattr(status, "region_id")
        assert hasattr(status, "mode")
        assert hasattr(status, "all_connectors_failed")
        assert hasattr(status, "degraded_connectors")
        assert status.region_id == "se_asia"


class TestEvent:
    """Test Event model."""

    def test_event_creation(self):
        """Test that events can be created."""
        event = Event(
            source="test",
            event_type="TEST_EVENT",
            severity="HIGH",
            lat=0.0,
            lon=0.0,
            timestamp=datetime.now(UTC),
            raw={"key": "value"},
        )

        assert event.source == "test"
        assert event.severity == "HIGH"

    def test_event_serialization(self):
        """Test that events can be serialized."""
        event = Event(
            source="test",
            event_type="TEST",
            severity="LOW",
            lat=10.0,
            lon=20.0,
            timestamp=datetime.now(UTC),
            raw={},
        )

        data = event.model_dump()
        assert "source" in data
        assert "event_type" in data


class TestFeedHealth:
    """Test FeedHealth model."""

    def test_feed_health_creation(self):
        """Test that FeedHealth can be created."""
        health = FeedHealth(
            connector="ais",
            status="HEALTHY",
            last_successful_fetch=datetime.now(UTC),
            last_latency_ms=100.0,
            event_count_last_hour=50,
            poll_interval_seconds=300,
        )

        assert health.connector == "ais"
        assert health.status == "HEALTHY"
