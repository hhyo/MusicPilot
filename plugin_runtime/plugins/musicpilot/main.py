"""FastAPI application entrypoint for MusicPilot Phase 1."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.health import build_health_payload
from .api.router import plugin_api_router, probe_api_router
from .core.config import settings
from .core.http import configure_logging, register_exception_handlers, register_http_middleware
from .core.responses import success_response
from .schemas.common import ApiResponse


def build_application() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_http_middleware(app)
    register_exception_handlers(app)

    @app.get("/", summary="Root information", include_in_schema=False)
    async def root(request: Request) -> ApiResponse:
        return success_response(
            request,
            data={
                "service": settings.app_name,
                "version": __version__,
                "phase": "Phase 1",
                "status": "probe-and-contract-skeleton-ready",
            },
            message="MusicPilot backend Phase 1 skeleton is running.",
            code="ROOT_OK",
            mock=False,
            note="This root endpoint confirms the backend skeleton is alive. Business capabilities are still placeholders.",
        )

    @app.get("/health", summary="Health check", tags=["Health"])
    async def health(request: Request) -> ApiResponse:
        return success_response(
            request,
            data=build_health_payload(),
            message="Health check passed.",
            code="HEALTH_OK",
            mock=False,
            note="This is application health only, not a real MoviePilot host capability probe.",
        )

    app.include_router(plugin_api_router, prefix=settings.api_prefix)
    app.include_router(probe_api_router, prefix="/api/probe")
    app.include_router(probe_api_router, prefix=f"{settings.api_prefix}/probe", include_in_schema=False)
    return app


app = build_application()

