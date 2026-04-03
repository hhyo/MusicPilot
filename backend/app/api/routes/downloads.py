"""Dispatch routes for the Phase 9 matrix-aware dispatch boundary."""

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
        note="当前 dispatch 会结合 Phase 8 真实矩阵优先选择更稳的 endpoint，并把 strategy decision、path handoff、verification 与 fallback 一并返回。若能力缺失、配置不完整、payload 不兼容或运行失败，会按策略回退到 mock。",
        todo=["继续把 `download_add` 从 single-sample 推进到 multi-sample 稳定成功。"],
    )
