"""Health-check routes and helpers for the backend skeleton."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from .. import __version__
from ..core.config import settings
from ..core.dependencies import (
    get_host_integration_service,
    get_host_strategy_service,
    get_validation_matrix_service,
)
from ..core.responses import success_response
from ..schemas.common import ApiResponse
from ..services.host_integration import HostIntegrationService
from ..services.host_strategy import HostStrategyService
from ..services.validation_matrix import HostValidationMatrixService

router = APIRouter(tags=["Health"])


def build_health_payload(
    runtime_state: dict,
    validation_matrix_summary: dict | None,
    strategy_summary: dict | None,
) -> dict:
    runtime_state = {**runtime_state, "strategy_summary": strategy_summary}
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "api_prefix": settings.api_prefix,
        "phase": "Phase 9",
        "host_integration": runtime_state,
        "validation_matrix": validation_matrix_summary,
        "strategy_summary": strategy_summary,
    }


@router.get("/health", summary="Namespaced health check")
async def health_check(
    request: Request,
    integration_service: HostIntegrationService = Depends(get_host_integration_service),
    validation_matrix_service: HostValidationMatrixService = Depends(get_validation_matrix_service),
    strategy_service: HostStrategyService = Depends(get_host_strategy_service),
) -> ApiResponse:
    summary = validation_matrix_service.summary()
    strategy_summary = strategy_service.summary()
    return success_response(
        request,
        data=build_health_payload(
            integration_service.runtime_state().model_dump(mode="json"),
            summary.model_dump(mode="json") if summary else None,
            strategy_summary.model_dump(mode="json"),
        ),
        message="Health check passed.",
        code="HEALTH_OK",
        mock=False,
        note=(
            "This endpoint confirms the FastAPI app is running and exposes the current host integration wiring state "
            "plus the latest real-host validation matrix summary and the current Phase 9 strategy summary."
        ),
    )
