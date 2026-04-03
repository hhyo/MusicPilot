"""Chart discovery routes for Phase 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_chart_service, get_subscription_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import EntityType
from ...schemas.orchestration import CreateChartEntrySubscriptionRequest
from ...services.charts import ChartService
from ...services.subscriptions import SubscriptionService

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get("/providers", summary="List chart providers")
async def chart_providers(
    request: Request,
    service: ChartService = Depends(get_chart_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_providers(),
        message="Chart providers loaded.",
        code="CHART_PROVIDERS_OK",
        mock=True,
        note="当前 provider 列表来自 mock chart source，尚未接入真实榜单抓取。",
    )


@router.get("", summary="List charts")
async def list_charts(
    request: Request,
    provider: str | None = Query(default=None),
    chart_type: EntityType | None = Query(default=None),
    region: str | None = Query(default=None),
    service: ChartService = Depends(get_chart_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_charts(provider=provider, chart_type=chart_type, region=region),
        message="Chart list loaded.",
        code="CHART_LIST_OK",
        mock=True,
        note="当前榜单列表来自 local seed / mock chart source，用于 Phase 4 的发现与订阅入口。",
    )


@router.get("/{chart_id}", summary="Get chart detail")
async def chart_detail(
    chart_id: str,
    request: Request,
    service: ChartService = Depends(get_chart_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_chart_detail(chart_id),
        message="Chart detail loaded.",
        code="CHART_DETAIL_OK",
        mock=True,
        note="当前榜单详情来自 mock chart source，榜单项可用于创建 Phase 4 最小订阅。",
    )


@router.post("/{chart_id}/subscribe", summary="Create subscription from chart entry")
async def subscribe_chart(
    chart_id: str,
    payload: CreateChartEntrySubscriptionRequest,
    request: Request,
    chart_service: ChartService = Depends(get_chart_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> ApiResponse:
    entry = chart_service.get_chart_entry(chart_id, payload.chart_item_id)
    return success_response(
        request,
        data=subscription_service.create_from_chart_entry(entry=entry, payload=payload),
        message="Subscription created from chart entry.",
        code="CHART_SUBSCRIBE_OK",
        mock=True,
        note="当前榜单订阅来自 mock chart entry，不会自动刷新或自动发现真实榜单增量。",
    )
