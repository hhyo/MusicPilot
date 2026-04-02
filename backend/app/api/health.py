"""Health-check routes and helpers for the backend skeleton."""

from fastapi import APIRouter

from .. import __version__
from ..core.config import settings
from ..core.responses import success_response
from ..schemas.common import ApiResponse

router = APIRouter(tags=["health"])


def build_health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "api_prefix": settings.api_prefix,
    }


@router.get("/health", summary="Namespaced health check")
async def health_check() -> ApiResponse:
    return success_response(data=build_health_payload(), message="Health check passed.")
