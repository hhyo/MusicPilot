"""HTTP middleware and exception handlers for request tracing."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .responses import error_json_response


LOGGER = logging.getLogger("musicpilot.http")


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def register_http_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        request.state.request_id = request_id

        started = perf_counter()
        LOGGER.info(
            "request.started request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception:
            LOGGER.exception(
                "request.failed request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise

        duration_ms = (perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        LOGGER.info(
            "request.completed request_id=%s status_code=%s duration_ms=%.2f",
            request_id,
            response.status_code,
            duration_ms,
        )
        return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed."
        return error_json_response(
            request,
            status_code=exc.status_code,
            code=f"HTTP_{exc.status_code}",
            message=message,
            data={"detail": exc.detail},
            note="The request did not complete successfully. This is the unified Phase 1 error envelope.",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_json_response(
            request,
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
            message="Request validation failed.",
            data={"errors": exc.errors()},
            note="Validation is handled centrally so probe and MVP routes keep the same response shape.",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        LOGGER.exception(
            "request.unhandled_exception request_id=%s path=%s",
            getattr(request.state, "request_id", "request-id-missing"),
            request.url.path,
        )
        return error_json_response(
            request,
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="Unexpected server error.",
            data={"detail": str(exc)},
            note="This is a Phase 1 fallback handler. Replace generic failures with domain errors in later phases.",
            todo=["Map domain exceptions to stable business error codes in later phases."],
        )

