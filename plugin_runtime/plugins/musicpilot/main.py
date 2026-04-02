"""FastAPI application entrypoint for MusicPilot Phase 0."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.health import build_health_payload
from .api.router import api_router
from .core.config import settings
from .core.responses import success_response
from .schemas.common import ApiResponse


def build_application() -> FastAPI:
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

    @app.get("/", summary="Root information", include_in_schema=False)
    async def root() -> ApiResponse:
        return success_response(
            data={
                "service": settings.app_name,
                "version": __version__,
                "phase": "Phase 0",
                "status": "skeleton-ready",
            },
            message="MusicPilot backend skeleton is running.",
        )

    @app.get("/health", summary="Health check", tags=["system"])
    async def health() -> ApiResponse:
        return success_response(data=build_health_payload(), message="Health check passed.")

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = build_application()
