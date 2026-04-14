"""Chart discovery routes for Phase 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...chain.subscribe import MusicSubscribeChain
from ...core.dependencies import get_music_chart_chain, get_music_subscribe_chain
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.shared import EntityType
from ...schemas.orchestration import CreateChartEntrySubscriptionRequest
from ...chain.chart import MusicChartChain

router = APIRouter(prefix="/charts", tags=["Charts"])


def _chart_note(mock: bool, *, subject: str) -> str:
    if mock:
        return f"当前{subject}来自 local seed / mock chart source，用于发现入口与订阅动作验证。"
    return f"当前{subject}来自真实 chart provider。"


@router.get("/providers", summary="List chart providers")
async def chart_providers(
    request: Request,
    chain: MusicChartChain = Depends(get_music_chart_chain),
) -> ApiResponse:
    data = chain.list_providers()
    mock = all(item.mock for item in data) if data else True
    return success_response(
        request,
        data=data,
        message="Chart providers loaded.",
        code="CHART_PROVIDERS_OK",
        mock=mock,
        note=_chart_note(mock, subject="provider 列表"),
    )


@router.get("", summary="List charts")
async def list_charts(
    request: Request,
    provider: str | None = Query(default=None),
    chart_type: EntityType | None = Query(default=None),
    region: str | None = Query(default=None),
    chain: MusicChartChain = Depends(get_music_chart_chain),
) -> ApiResponse:
    data = chain.list_charts(provider=provider, chart_type=chart_type, region=region)
    return success_response(
        request,
        data=data,
        message="Chart list loaded.",
        code="CHART_LIST_OK",
        mock=data.mock,
        note=data.note,
    )


@router.get("/{chart_id}", summary="Get chart detail")
async def chart_detail(
    chart_id: str,
    request: Request,
    chain: MusicChartChain = Depends(get_music_chart_chain),
) -> ApiResponse:
    data = chain.get_chart_detail(chart_id)
    return success_response(
        request,
        data=data,
        message="Chart detail loaded.",
        code="CHART_DETAIL_OK",
        mock=data.mock,
        note=data.note,
    )


@router.get("/{chart_id}/runtime", summary="Get chart runtime status")
async def chart_runtime(
    chart_id: str,
    request: Request,
    chain: MusicChartChain = Depends(get_music_chart_chain),
) -> ApiResponse:
    data = chain.get_chart_runtime(chart_id)
    return success_response(
        request,
        data=data,
        message="Chart runtime loaded.",
        code="CHART_RUNTIME_OK",
        mock=data.mock,
        note=data.note,
    )


@router.post("/{chart_id}/refresh", summary="Refresh chart runtime and detail snapshot")
async def refresh_chart(
    chart_id: str,
    request: Request,
    chain: MusicChartChain = Depends(get_music_chart_chain),
) -> ApiResponse:
    data = chain.refresh_chart(chart_id)
    return success_response(
        request,
        data=data,
        message="Chart refreshed.",
        code="CHART_REFRESH_OK",
        mock=data.mock,
        note=data.note,
    )


@router.post("/{chart_id}/subscribe", summary="Create subscription from chart entry")
async def subscribe_chart(
    chart_id: str,
    payload: CreateChartEntrySubscriptionRequest,
    request: Request,
    chart_chain: MusicChartChain = Depends(get_music_chart_chain),
    subscribe_chain: MusicSubscribeChain = Depends(get_music_subscribe_chain),
) -> ApiResponse:
    entry = chart_chain.get_discovery_entry(chart_id, payload.chart_item_id)
    data = subscribe_chain.create_from_chart_entry(entry=entry, payload=payload)
    return success_response(
        request,
        data=data,
        message="Subscription created from chart entry.",
        code="CHART_SUBSCRIBE_OK",
        mock=entry.entry.mock,
        note=(
            "当前榜单订阅来自 mock chart entry，不会参与真实榜单刷新。"
            if entry.entry.mock
            else "当前榜单订阅来自真实 chart entry，会复用持久化榜单数据与统一周期刷新。"
        ),
    )
