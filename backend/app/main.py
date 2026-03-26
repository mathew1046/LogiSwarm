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
from app.middleware import RequestIDMiddleware

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


validate_env()
configure_logging()

app = FastAPI(title="LogiSwarm Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(CORSMiddleware, **_cors_config())

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler_custom)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

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
