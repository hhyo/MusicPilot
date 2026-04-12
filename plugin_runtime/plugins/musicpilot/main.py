"""FastAPI application entrypoint for the simplified semantic-driven runtime."""

from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.health import build_health_payload
from .api.router import plugin_api_router, probe_api_router
from .core.config import settings
from .core.dependencies import (
    build_subscription_scheduler_service,
    get_host_integration_service,
    get_session_factory,
    get_validation_matrix_service,
)
from .core.http import configure_logging, register_exception_handlers, register_http_middleware
from .core.responses import success_response
from .schemas.common import ApiResponse
from .services.host_integration import HostIntegrationService
from .services.metadata import bootstrap_metadata_storage
from .services.validation_matrix import HostValidationMatrixService


logger = logging.getLogger("musicpilot.scheduler")


async def _run_subscription_scheduler_loop() -> None:
    session_factory = get_session_factory()
    while True:
        try:
            with session_factory() as session:
                scheduler = build_subscription_scheduler_service(session)
                result = scheduler.run_pending_once()
                if result["executed_ids"]:
                    logger.info("subscription.scheduler.executed ids=%s", ",".join(result["executed_ids"]))
                if result["error_ids"]:
                    logger.warning("subscription.scheduler.errors ids=%s", ",".join(result["error_ids"]))
                handoff_reconcile = result.get("handoff_reconcile") or {}
                if handoff_reconcile.get("applied_run_ids"):
                    logger.info(
                        "subscription.scheduler.handoff_applied run_ids=%s",
                        ",".join(handoff_reconcile["applied_run_ids"]),
                    )
                if handoff_reconcile.get("unresolved_run_ids"):
                    logger.warning(
                        "subscription.scheduler.handoff_unresolved run_ids=%s",
                        ",".join(handoff_reconcile["unresolved_run_ids"]),
                    )
                session.commit()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("subscription.scheduler.loop_failed")
        await asyncio.sleep(settings.subscription_scheduler_poll_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_metadata_storage()
    scheduler_task = None
    if settings.subscription_scheduler_enabled:
        scheduler_task = asyncio.create_task(_run_subscription_scheduler_loop())
    try:
        yield
    finally:
        if scheduler_task is not None:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass


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
                "phase": "Architecture Simplification",
                "status": "semantic-driven-runtime",
                "host_integration": integration_service.runtime_state().model_dump(mode="json"),
            },
            message="MusicPilot backend runtime is running.",
            code="ROOT_OK",
            mock=False,
            note="This root endpoint confirms host-aware search, dispatch, path handoff, and organize wiring are alive.",
        )

    @app.get("/health", summary="Health check", tags=["Health"])
    async def health(
        request: Request,
        integration_service: HostIntegrationService = Depends(get_host_integration_service),
        validation_matrix_service: HostValidationMatrixService = Depends(get_validation_matrix_service),
    ) -> ApiResponse:
        summary = validation_matrix_service.summary()
        return success_response(
            request,
            data=build_health_payload(
                integration_service.runtime_state().model_dump(mode="json"),
                summary.model_dump(mode="json") if summary else None,
            ),
            message="Health check passed.",
            code="HEALTH_OK",
            mock=False,
            note=(
                "This is application health plus current host integration wiring and the latest verification artifact summary. "
                "It does not change runtime semantics and does not prove every MoviePilot host capability has been verified."
            ),
        )

    app.include_router(plugin_api_router, prefix=settings.api_prefix)
    app.include_router(probe_api_router, prefix="/api/probe")
    app.include_router(probe_api_router, prefix=f"{settings.api_prefix}/probe", include_in_schema=False)
    return app


app = build_application()
