"""Health-check routes and helpers for the backend skeleton."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from .. import __version__
from ..core.config import settings
from ..core.dependencies import get_host_integration_service
from ..core.responses import success_response
from ..schemas.common import ApiResponse
from ..services.host_integration import HostIntegrationService

router = APIRouter(tags=["Health"])


def build_health_payload(runtime_state: dict) -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "api_prefix": settings.api_prefix,
        "phase": "Phase 6",
        "host_integration": runtime_state,
    }


@router.get("/health", summary="Namespaced health check")
async def health_check(
    request: Request,
    integration_service: HostIntegrationService = Depends(get_host_integration_service),
) -> ApiResponse:
    return success_response(
        request,
        data=build_health_payload(integration_service.runtime_state().model_dump(mode="json")),
        message="Health check passed.",
        code="HEALTH_OK",
        mock=False,
        note="This endpoint confirms the FastAPI app is running and exposes the current host integration wiring state.",
    )
