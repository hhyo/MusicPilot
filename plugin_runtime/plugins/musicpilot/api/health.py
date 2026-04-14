"""Health-check routes and helpers for the backend skeleton."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from .. import __version__
from ..chain.system import MusicSystemChain
from ..core.dependencies import get_music_system_chain
from ..core.responses import success_response
from ..schemas.common import ApiResponse

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Namespaced health check")
async def health_check(
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
            "This endpoint confirms the FastAPI app is running and exposes the current host integration wiring state "
            "plus the latest real-host verification artifact summary."
        ),
    )
