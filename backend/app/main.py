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

__version__ = "0.2.0"

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


def _ensure_utf8_stdout() -> None:
    if sys.platform == "win32" and sys.stdout.encoding != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")


_ensure_utf8_stdout()

from app.config import validate_env
from app.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler_custom,
    validation_exception_handler,
)
from app.middleware import RequestIDMiddleware, SecurityHeadersMiddleware

from app.agents.agent_manager import agent_manager
from app.api import (
    actions_router,
    agents_ext_router,
    agents_router,
    analytics_router,
    anomaly_router,
    auth_router,
    disruptions_router,
    export_router,
    feeds_router,
    metrics_router,
    orchestrator_router,
    projects_router,
    recommendations_router,
    reports_router,
    reroute_router,
    routes_router,
    scenarios_router,
    shipments_router,
    sse_router,
    webhooks_router,
    websocket_router,
)
from app.api.shipments import start_risk_evaluator
from app.bus.connection import close_redis_pool, init_redis_pool
from app.db.session import engine
from app.orchestrator.eta_recalculator import eta_recalculator
from app.orchestrator.orchestrator import swarm_orchestrator
from app.shutdown import register_shutdown_handler, setup_signal_handlers


class MaxTokensWarningFilter(logging.Filter):
    """Suppress repetitive max-tokens warnings from provider/client loggers."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        return "max token" not in message and "max_tokens" not in message


def _configure_stdlib_logging_filter() -> None:
    filter_instance = MaxTokensWarningFilter()
    for target_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        target_logger = logging.getLogger(target_name)
        target_logger.addFilter(filter_instance)


def configure_logging() -> None:
    """Configure structured logging via loguru and filter noisy token warnings."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=os.getenv("LOG_LEVEL", "INFO"),
        serialize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
    _configure_stdlib_logging_filter()


validate_env()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_logs: List[Dict[str, Any]] = []
    startup_logs.append(
        {
            "event": "startup",
            "message": "Initializing LogiSwarm backend",
            "version": __version__,
        }
    )

    await init_redis_pool()
    startup_logs.append(
        {"event": "startup", "component": "redis", "status": "connected"}
    )

    await swarm_orchestrator.start()
    startup_logs.append(
        {"event": "startup", "component": "orchestrator", "status": "started"}
    )

    await agent_manager.start_all()
    startup_logs.append(
        {"event": "startup", "component": "agents", "count": len(agent_manager.agents)}
    )

    await eta_recalculator.start()
    startup_logs.append(
        {"event": "startup", "component": "eta_recalculator", "status": "started"}
    )

    await start_risk_evaluator()
    startup_logs.append(
        {"event": "startup", "component": "risk_evaluator", "status": "started"}
    )

    register_shutdown_handler(lambda: swarm_orchestrator.stop())
    register_shutdown_handler(lambda: agent_manager.stop_all())
    register_shutdown_handler(lambda: eta_recalculator.stop())
    register_shutdown_handler(lambda: close_redis_pool())

    for entry in startup_logs:
        logger.info(entry)

    _print_route_table(app)
    yield

    logger.info({"event": "shutdown", "message": "Shutting down LogiSwarm backend"})


def _print_route_table(app: FastAPI) -> None:
    routes: List[Dict[str, str]] = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                if method != "HEAD":
                    routes.append({"method": method, "path": route.path})
    routes.sort(key=lambda r: r["path"])
    max_method_len = max(len(r["method"]) for r in routes) if routes else 7
    header = f"{'METHOD':<{max_method_len}} PATH"
    logger.info({"event": "route_table", "header": header})
    for r in routes:
        logger.info({"event": "route", "method": r["method"], "path": r["path"]})


def _cors_config():
    """Get CORS configuration from environment."""
    origins_str = os.getenv("CORS_ALLOW_ORIGINS", "")
    if origins_str:
        origins = [origin.strip() for origin in origins_str.split(",")]
    else:
        origins = ["*"]  # Allow all in development

    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


app = FastAPI(title="LogiSwarm Backend", version=__version__, lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(CORSMiddleware, **_cors_config())

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler_custom)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(projects_router)
app.include_router(feeds_router)
app.include_router(agents_router)
app.include_router(agents_ext_router)
app.include_router(orchestrator_router)
app.include_router(actions_router)
app.include_router(shipments_router)
app.include_router(routes_router)
app.include_router(reports_router)
app.include_router(sse_router)
app.include_router(metrics_router)
app.include_router(recommendations_router)
app.include_router(disruptions_router)
app.include_router(anomaly_router)
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(scenarios_router)
app.include_router(webhooks_router)
app.include_router(export_router)
app.include_router(analytics_router)
app.include_router(reroute_router)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": __version__}
