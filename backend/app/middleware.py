import uuid
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        logger.bind(
            event="request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        ).debug(f"{request.method} {request.url.path} - {response.status_code}")

        return response
