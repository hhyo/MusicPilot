"""Charts route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import CreateChartSubscriptionRequest
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get("/providers", summary="Get chart providers placeholder")
async def chart_providers(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.chart_providers(),
        message="Chart providers placeholder is callable.",
        code="CHART_PROVIDERS_PLACEHOLDER",
        mock=True,
        note="当前 provider 列表为占位结构，未连接真实榜单源。",
    )


@router.get("", summary="Get charts placeholder")
async def list_charts(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_charts(),
        message="Chart list placeholder is callable.",
        code="CHART_LIST_PLACEHOLDER",
        mock=True,
        note="当前榜单列表为 mock 数据，待后续接入真实 chart provider。",
    )


@router.get("/{chart_id}", summary="Get chart detail placeholder")
async def chart_detail(
    chart_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.chart_detail(chart_id),
        message="Chart detail placeholder is callable.",
        code="CHART_DETAIL_PLACEHOLDER",
        mock=True,
        note="当前榜单详情为 mock 数据，待后续接入真实榜单条目。",
    )


@router.post("/{chart_id}/subscribe", summary="Create chart subscription placeholder")
async def subscribe_chart(
    chart_id: str,
    payload: CreateChartSubscriptionRequest,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.create_chart_subscription(chart_id, payload),
        message="Chart subscription placeholder accepted the payload.",
        code="CHART_SUBSCRIBE_PLACEHOLDER",
        mock=True,
        note="当前仅验证榜单订阅契约，不会创建真实订阅任务。",
    )

