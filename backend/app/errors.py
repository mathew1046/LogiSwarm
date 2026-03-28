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

import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class ErrorResponse(BaseModel):
    error: str
    code: str
    detail: Optional[Dict[str, Any]] = None
    request_id: str


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = str(uuid.uuid4())

    field_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Invalid value")
        field_errors.append({"field": field, "message": message})

    logger.bind(
        event="validation_error",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        errors=field_errors,
    ).warning(f"Validation error: {len(field_errors)} field(s) failed")

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        headers={"X-Request-ID": request_id},
        content={
            "error": "Validation failed",
            "code": "VALIDATION_ERROR",
            "detail": {"fields": field_errors},
            "request_id": request_id,
        },
    )


async def http_exception_handler_custom(
    request: Request, exc: HTTPException
) -> JSONResponse:
    request_id = str(uuid.uuid4())

    logger.bind(
        event="http_error",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=str(exc.detail),
    ).warning(f"HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-ID": request_id},
        content={
            "error": str(exc.detail),
            "code": f"HTTP_{exc.status_code}",
            "detail": None,
            "request_id": request_id,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())

    logger.bind(
        event="unhandled_error",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error_message=str(exc),
    ).exception(f"Unhandled exception: {exc}")

    error_message = str(exc)

    if "sql" in error_message.lower() or "query" in error_message.lower():
        error_message = "Database operation failed"

    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        headers={"X-Request-ID": request_id},
        content={
            "error": error_message,
            "code": "INTERNAL_ERROR",
            "detail": None,
            "request_id": request_id,
        },
    )


class AppException(Exception):
    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = str(uuid.uuid4())

    logger.bind(
        event="app_error",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error_code=exc.code,
        error_message=exc.message,
    ).warning(f"Application error: {exc.code} - {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-ID": request_id},
        content={
            "error": exc.message,
            "code": exc.code,
            "detail": exc.detail,
            "request_id": request_id,
        },
    )
