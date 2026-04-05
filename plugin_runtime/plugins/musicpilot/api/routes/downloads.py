"""Dispatch routes for the host-aware dispatch boundary."""

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
        note=(
            "当前 dispatch 只按输入语义走固定路径：有 `media_in` 走 `/api/v1/download/`；"
            "只有 torrent 但已具备宿主媒体参考时走 `/api/v1/download/add`；"
            "音乐 torrent-only 候选则走宿主 downloader runtime 直接提交下载器。"
            "响应会直接暴露 backend、verification、path handoff 与失败原因。"
        ),
        todo=["继续扩展真实成功样例，但不再让验证矩阵直接驱动运行时决策。"],
    )
