from app.api.actions import router as actions_router
from app.api.feeds import router as feeds_router
from app.api.orchestrator import router as orchestrator_router
from app.api.projects import router as projects_router
from app.api.routes import router as routes_router
from app.api.shipments import router as shipments_router
from app.api.sse import router as sse_router
from app.agents.agent_manager import router as agents_router

__all__ = [
    "projects_router",
    "feeds_router",
    "agents_router",
    "orchestrator_router",
    "actions_router",
    "shipments_router",
    "sse_router",
    "routes_router",
]
