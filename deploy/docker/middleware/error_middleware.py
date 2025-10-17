# deploy/docker/error_middleware.py

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.error_context import ErrorContext, set_correlation_id


logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Centralized error handling middleware.

    Replaces per-endpoint error handling with a single middleware layer that:
    - Sets correlation IDs for request tracking
    - Catches all unhandled exceptions
    - Converts them to structured error responses
    - Logs errors with full context
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", "")
        if not correlation_id:
            error_ctx = ErrorContext.from_exception(Exception())
            correlation_id = error_ctx.correlation_id

        set_correlation_id(correlation_id)

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as exc:
            logger.exception(
                "Unhandled exception during request processing [%s]",
                correlation_id,
                extra={
                    "correlation_id": correlation_id,
                    "path": request.url.path,
                    "method": request.method,
                },
            )

            error_ctx = ErrorContext.from_exception(
                exc,
                operation=f"{request.method} {request.url.path}"
            )
            error_ctx.correlation_id = correlation_id
            error_ctx.log()

            error_response = error_ctx.to_error_response()

            status_code = 500
            if error_ctx.error_type == "validation":
                status_code = 400
            elif error_ctx.error_type == "not_found":
                status_code = 404
            elif error_ctx.error_type == "security":
                status_code = 403
            elif error_ctx.error_type == "size_limit":
                status_code = 413

            return JSONResponse(
                status_code=status_code,
                content=error_response.model_dump(),
                headers={"X-Correlation-ID": correlation_id},
            )