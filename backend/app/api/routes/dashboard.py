"""Dashboard route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="Get dashboard summary placeholder")
async def dashboard_summary(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.dashboard_summary(),
        message="Dashboard summary placeholder is callable.",
        code="DASHBOARD_SUMMARY_PLACEHOLDER",
        mock=True,
        note="当前是 dashboard 模块的 mock 摘要数据，待后续接入真实聚合服务。",
        todo=["Replace placeholder counters with aggregated task and subscription data."],
    )

