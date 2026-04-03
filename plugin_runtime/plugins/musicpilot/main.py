"""FastAPI application entrypoint for MusicPilot Phase 6."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.health import build_health_payload
from .api.router import plugin_api_router, probe_api_router
from .core.config import settings
from .core.dependencies import get_host_integration_service
from .core.http import configure_logging, register_exception_handlers, register_http_middleware
from .core.responses import success_response
from .schemas.common import ApiResponse
from .services.host_integration import HostIntegrationService
from .services.metadata import bootstrap_metadata_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_metadata_storage()
    yield


def build_application() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
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
    async def root(
        request: Request,
        integration_service: HostIntegrationService = Depends(get_host_integration_service),
    ) -> ApiResponse:
        return success_response(
            request,
            data={
                "service": settings.app_name,
                "version": __version__,
                "phase": "Phase 6",
                "status": "host-aware-search-dispatch-organize-ready",
                "host_integration": integration_service.runtime_state().model_dump(mode="json"),
            },
            message="MusicPilot backend Phase 6 host-aware organize loop is running.",
            code="ROOT_OK",
            mock=False,
            note="This root endpoint confirms host-aware search, dispatch, and organize resolution are alive. Real MoviePilot host verification remains separate from this runtime status.",
        )

    @app.get("/health", summary="Health check", tags=["Health"])
    async def health(
        request: Request,
        integration_service: HostIntegrationService = Depends(get_host_integration_service),
    ) -> ApiResponse:
        return success_response(
            request,
            data=build_health_payload(integration_service.runtime_state().model_dump(mode="json")),
            message="Health check passed.",
            code="HEALTH_OK",
            mock=False,
            note="This is application health plus current host integration wiring summary; it is not a proof that every MoviePilot host capability has been verified.",
        )

    app.include_router(plugin_api_router, prefix=settings.api_prefix)
    app.include_router(probe_api_router, prefix="/api/probe")
    app.include_router(probe_api_router, prefix=f"{settings.api_prefix}/probe", include_in_schema=False)
    return app


app = build_application()
