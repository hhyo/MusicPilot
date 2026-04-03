"""Dispatch routes for the Phase 7B host-aware dispatch boundary."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_dispatch_service
from ...core.responses import success_response
from ...schemas.acquisition import DispatchRequest, DispatchResult
from ...schemas.common import TypedApiResponse
from ...services.dispatch import DispatchService

router = APIRouter(prefix="/downloads", tags=["Downloads"])


@router.post(
    "/dispatch",
    summary="Dispatch a candidate to the downloader boundary",
    response_model=TypedApiResponse[DispatchResult],
)
async def dispatch_download(
    payload: DispatchRequest,
    request: Request,
    service: DispatchService = Depends(get_dispatch_service),
) -> TypedApiResponse[DispatchResult]:
    result = service.dispatch(payload)
    return success_response(
        request,
        data=result,
        message="Dispatch boundary handled the candidate.",
        code="DISPATCH_BOUNDARY_OK",
        mock=result.dispatch_backend == "mock",
        note="当前 dispatch 会优先尝试真实 MoviePilot download 语义；成功派发后会尽量把 download hash 回灌成 host path handoff，供 organize 继续消费。若能力缺失、配置不完整、payload 不兼容或运行失败，会按策略回退到 mock。",
        todo=["继续补充更多真实 MoviePilot 成功派发样例，并确认音乐资源在宿主中的最终可识别语义。"],
    )
