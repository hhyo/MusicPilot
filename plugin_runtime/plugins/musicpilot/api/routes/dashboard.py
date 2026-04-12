"""Dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_dashboard_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="Get dashboard summary")
async def dashboard_summary(
    request: Request,
    service: DashboardService = Depends(get_dashboard_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.summary(),
        message="Dashboard summary loaded.",
        code="DASHBOARD_SUMMARY_OK",
        mock=False,
        note="当前 dashboard 摘要只聚合现有 provider、discovery、handoff、organize 与 scheduler 状态，不伪造探测成功。",
    )
