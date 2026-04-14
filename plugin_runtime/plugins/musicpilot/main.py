"""FastAPI application entrypoint for the simplified semantic-driven runtime."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .chain.system import MusicSystemChain
from .api.router import plugin_api_router, probe_api_router
from .core.config import settings
from .core.dependencies import (
    get_music_system_chain,
)
from .core.http import configure_logging, register_exception_handlers, register_http_middleware
from .core.responses import success_response
from .schemas.common import ApiResponse
from .startup.bootstrap import bootstrap_runtime_storage
from .startup.scheduler import build_local_scheduler_tasks, should_start_local_scheduler_loop


logger = logging.getLogger("musicpilot.scheduler")


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_runtime_storage()
    scheduler_tasks: list[asyncio.Task] = []
    if should_start_local_scheduler_loop():
        scheduler_tasks = [asyncio.create_task(task) for task in build_local_scheduler_tasks()]
    try:
        yield
    finally:
        for task in scheduler_tasks:
            task.cancel()
        for task in scheduler_tasks:
            try:
                await task
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
        chain: MusicSystemChain = Depends(get_music_system_chain),
    ) -> ApiResponse:
        return success_response(
            request,
            data=chain.root_payload(version=__version__),
            message="MusicPilot backend runtime is running.",
            code="ROOT_OK",
            mock=False,
            note="This root endpoint confirms host-aware search, dispatch, path handoff, and organize wiring are alive.",
        )

    @app.get("/health", summary="Health check", tags=["Health"])
    async def health(
        request: Request,
        chain: MusicSystemChain = Depends(get_music_system_chain),
    ) -> ApiResponse:
        return success_response(
            request,
            data=chain.health_payload(version=__version__),
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
