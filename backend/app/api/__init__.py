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

from app.api.actions import router as actions_router
from app.api.agents_ext import router as agents_ext_router
from app.api.analytics import router as analytics_router
from app.api.anomaly import router as anomaly_router
from app.api.auth import router as auth_router
from app.api.disruptions import router as disruptions_router
from app.api.export_webhooks import export_router, router as webhooks_router
from app.api.feeds import router as feeds_router
from app.api.metrics import router as metrics_router
from app.api.orchestrator import router as orchestrator_router
from app.api.projects import router as projects_router
from app.api.recommendations import router as recommendations_router
from app.api.reports import router as reports_router
from app.api.routes import router as routes_router
from app.api.scenarios import router as scenarios_router
from app.api.shipments import router as shipments_router
from app.api.sse import router as sse_router
from app.api.websocket import router as websocket_router
from app.agents.agent_manager import router as agents_router

__all__ = [
    "projects_router",
    "feeds_router",
    "agents_router",
    "agents_ext_router",
    "orchestrator_router",
    "actions_router",
    "shipments_router",
    "sse_router",
    "routes_router",
    "reports_router",
    "metrics_router",
    "recommendations_router",
    "disruptions_router",
    "anomaly_router",
    "auth_router",
    "websocket_router",
    "scenarios_router",
    "webhooks_router",
    "export_router",
    "analytics_router",
]
