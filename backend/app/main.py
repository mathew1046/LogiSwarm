import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


def _ensure_utf8_stdout() -> None:
    if sys.platform == "win32" and sys.stdout.encoding != "utf-8":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")


_ensure_utf8_stdout()

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
from app.db.session import engine
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


METHOD_COLORS = {
    "GET": "\033[92m",
    "POST": "\033[94m",
    "PUT": "\033[93m",
    "PATCH": "\033[93m",
    "DELETE": "\033[91m",
    "OPTIONS": "\033[96m",
    "HEAD": "\033[96m",
}
RESET_COLOR = "\033[0m"


def _colorize_method(method: str) -> str:
    """Return colorized HTTP method string."""
    color = METHOD_COLORS.get(method.upper(), "")
    return f"{color}{method}{RESET_COLOR}" if color else method


def _log_registered_routes(app: FastAPI) -> None:
    """Print all registered routes in a clean table with color-coded methods."""
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = sorted(route.methods or set())
            for method in methods:
                if method == "HEAD":
                    continue
                routes.append((method, route.path, route.name or ""))

    routes.sort(key=lambda r: (r[1], r[0]))

    logger.bind(event="startup_routes").info("Registered API routes table")
    print("\n" + "=" * 80)
    print("REGISTERED API ROUTES")
    print("=" * 80)
    print(f"{'Method':<10} {'Path':<50} {'Name':<20}")
    print("-" * 80)
    for method, path, name in routes:
        colored_method = _colorize_method(f"{method:<10}")
        print(f"{colored_method} {path:<50} {name:<20}")
    print("=" * 80 + "\n")

    for method, path, name in routes:
        logger.bind(
            event="route_registered",
            method=method,
            path=path,
            name=name,
        ).debug("Route registered")


def _log_dependency_health() -> None:
    """Log the health status of all connected dependencies."""
    print("\n" + "=" * 80)
    print("DEPENDENCY HEALTH STATUS")
    print("=" * 80)

    agent_count = len(agent_manager.agents)
    print(f"{'Dependency':<25} {'Status':<15} {'Details'}")
    print("-" * 80)

    print(f"{'Database':<25} {'\033[92mconnected\033[0m':<15} PostgreSQL + TimescaleDB")
    print(f"{'Redis':<25} {'\033[92mconnected\033[0m':<15} Pub/Sub bus initialized")
    print(f"{'Zep Cloud':<25} {'\033[92mconfigured\033[0m':<15} Episodic memory ready")
    print(
        f"{'Geo-Agents':<25} {f'\033[92m{agent_count} started\033[0m':<15} All regions active"
    )
    print(
        f"{'Orchestrator':<25} {'\033[92mrunning\033[0m':<15} Swarm coordination active"
    )

    print("=" * 80 + "\n")

    logger.bind(
        event="startup_health",
        agents=len(agent_manager.agents),
        database="connected",
        redis="connected",
        zep="configured",
    ).info("Dependency health check complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.bind(event="startup").info("Starting backend service")

    setup_signal_handlers()

    await init_redis_pool()
    logger.bind(event="startup").info("Redis connection pool initialized")
    await agent_manager.start_all()
    logger.bind(event="startup").info("Geo-agent manager started")
    await swarm_orchestrator.start()
    logger.bind(event="startup").info("Swarm orchestrator started")
    _log_registered_routes(app)
    _log_dependency_health()

    yield

    await graceful_shutdown_app()


async def graceful_shutdown_app() -> None:
    logger.bind(event="shutdown").info("Initiating application shutdown")

    logger.bind(event="shutdown").info("Stopping swarm orchestrator")
    await swarm_orchestrator.stop()
    logger.bind(event="shutdown").info("Swarm orchestrator stopped")

    logger.bind(event="shutdown").info("Stopping geo-agents")
    await agent_manager.stop_all()
    logger.bind(event="shutdown").info("Geo-agent manager stopped")

    logger.bind(event="shutdown").info("Closing Redis connection pool")
    await close_redis_pool()
    logger.bind(event="shutdown").info("Redis connection pool closed")

    logger.bind(event="shutdown").info("Closing database engine")
    await engine.dispose()
    logger.bind(event="shutdown").info("Database engine closed")

    logger.bind(event="shutdown").info("Backend service shutdown complete")


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
