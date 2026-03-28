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

"""
Locust load testing for LogiSwarm API.

Run with:
    locust -f locustfile.py --host http://localhost:5001

Scenarios:
- 100 concurrent users viewing dashboard
- 50 concurrent SSE connections
- Rapid disruption event injection
"""

import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


class LogiSwarmUser(HttpUser):
    """Simulates a user viewing the dashboard and interacting with agents."""

    wait_time = between(1, 5)

    def on_start(self):
        """Initialize user session."""
        self.project_id = None
        self.auth_token = None

    @task(10)
    def get_health(self):
        """Health check endpoint - most frequent."""
        self.client.get("/health", name="/health")

    @task(5)
    def get_projects(self):
        """List all projects."""
        self.client.get("/api/projects", name="/api/projects")

    @task(3)
    def get_agents(self):
        """Get agent status for a project."""
        if self.project_id:
            self.client.get(
                f"/api/projects/{self.project_id}/agents",
                name="/api/projects/{id}/agents",
            )

    @task(2)
    def get_feeds(self):
        """Get feed events for a project."""
        if self.project_id:
            self.client.get(
                f"/api/projects/{self.project_id}/feeds/events",
                name="/api/projects/{id}/feeds/events",
            )

    @task(2)
    def get_disruptions(self):
        """Get disruption events."""
        if self.project_id:
            self.client.get(
                f"/api/projects/{self.project_id}/disruptions",
                name="/api/projects/{id}/disruptions",
            )

    @task(1)
    def get_recommendations(self):
        """Get route recommendations."""
        if self.project_id:
            self.client.get(
                f"/api/projects/{self.project_id}/recommendations",
                name="/api/projects/{id}/recommendations",
            )

    @task(1)
    def get_analytics(self):
        """Get analytics dashboard data."""
        self.client.get("/api/analytics/summary", name="/api/analytics/summary")


class AdminUser(HttpUser):
    """Simulates an admin performing management operations."""

    wait_time = between(2, 10)

    @task(5)
    def get_metrics(self):
        """Get Prometheus metrics."""
        self.client.get("/metrics", name="/metrics")

    @task(3)
    def get_agent_details(self):
        """Get detailed agent information."""
        regions = [
            "gulf_suez",
            "se_asia",
            "europe",
            "north_america",
            "china_ea",
            "south_asia",
            "latin_america",
            "africa",
        ]
        region = random.choice(regions)
        self.client.get(f"/api/agents/{region}", name="/api/agents/{region}")


class DisruptionSpamUser(HttpUser):
    """Simulates rapid disruption event injection (stress test)."""

    wait_time = between(0.5, 2)

    @task
    def inject_disruption(self):
        """Inject disruption events rapidly."""
        regions = [
            "gulf_suez",
            "se_asia",
            "europe",
            "north_america",
            "china_ea",
            "south_asia",
            "latin_america",
            "africa",
        ]
        severities = ["low", "medium", "high", "critical"]

        payload = {
            "region_id": random.choice(regions),
            "severity": random.choice(severities),
            "signal_type": random.choice(
                ["weather", "port_congestion", "geopolitical", "vessel_delay"]
            ),
            "description": f"Load test disruption event",
            "latitude": random.uniform(-90, 90),
            "longitude": random.uniform(-180, 180),
        }

        self.client.post(
            "/api/disruptions", json=payload, name="/api/disruptions [POST]"
        )


class SSEConnectionUser(HttpUser):
    """Simulates SSE event stream connections."""

    wait_time = between(30, 60)

    @task
    def connect_sse(self):
        """Connect to SSE event stream."""
        if self.project_id:
            with self.client.get(
                f"/api/projects/{self.project_id}/events/stream",
                name="/api/projects/{id}/events/stream",
                stream=True,
                timeout=30,
            ) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Setup before test starts."""
    print("Starting LogiSwarm load test...")
    if isinstance(environment.runner, (MasterRunner, WorkerRunner)):
        print("Running in distributed mode")
    else:
        print("Running in standalone mode")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Cleanup after test stops."""
    print("LogiSwarm load test completed.")
