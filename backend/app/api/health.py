"""Health-check routes and helpers for the backend skeleton."""

from __future__ import annotations

from fastapi import APIRouter, Request

from .. import __version__
from ..core.config import settings
from ..core.responses import success_response
from ..schemas.common import ApiResponse

router = APIRouter(tags=["Health"])


def build_health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "api_prefix": settings.api_prefix,
        "phase": "Phase 1",
    }


@router.get("/health", summary="Namespaced health check")
async def health_check(request: Request) -> ApiResponse:
    return success_response(
        request,
        data=build_health_payload(),
        message="Health check passed.",
        code="HEALTH_OK",
        mock=False,
        note="This endpoint confirms the FastAPI app is running. It does not validate real host integration.",
    )

