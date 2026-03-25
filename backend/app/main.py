import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.agents.agent_manager import agent_manager
from app.api import (
    actions_router,
    agents_router,
    feeds_router,
    orchestrator_router,
    projects_router,
    reports_router,
    routes_router,
    shipments_router,
    sse_router,
)
from app.bus.connection import close_redis_pool, init_redis_pool
from app.orchestrator.orchestrator import swarm_orchestrator


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


def _cors_config() -> Dict[str, Any]:
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    if environment in {"dev", "development", "local"}:
        return {
            "allow_origins": ["*"],
            "allow_credentials": False,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

    allowed_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
    allowed_origins: List[str] = [
        origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()
    ]

    return {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


def _log_registered_routes(app: FastAPI) -> None:
    logger.bind(event="startup_routes").info("Registered API routes")
    for route in app.routes:
        methods = ",".join(sorted(route.methods or []))
        logger.bind(
            event="route_registered",
            method=methods,
            path=route.path,
            name=route.name,
        ).info("Route")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.bind(event="startup").info("Starting backend service")
    await init_redis_pool()
    logger.bind(event="startup").info("Redis connection pool initialized")
    await agent_manager.start_all()
    logger.bind(event="startup").info("Geo-agent manager started")
    await swarm_orchestrator.start()
    logger.bind(event="startup").info("Swarm orchestrator started")
    _log_registered_routes(app)
    yield
    await swarm_orchestrator.stop()
    logger.bind(event="shutdown").info("Swarm orchestrator stopped")
    await agent_manager.stop_all()
    logger.bind(event="shutdown").info("Geo-agent manager stopped")
    await close_redis_pool()
    logger.bind(event="shutdown").info("Redis connection pool closed")
    logger.bind(event="shutdown").info("Shutting down backend service")


configure_logging()

app = FastAPI(title="LogiSwarm Backend", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, **_cors_config())
app.include_router(projects_router)
app.include_router(feeds_router)
app.include_router(agents_router)
app.include_router(orchestrator_router)
app.include_router(actions_router)
app.include_router(shipments_router)
app.include_router(routes_router)
app.include_router(reports_router)
app.include_router(sse_router)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
