"""Dispatch routes for the host-aware dispatch boundary."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_dispatch_service, get_downloads_workspace_service
from ...core.responses import success_response
from ...schemas.acquisition import (
    DispatchRequest,
    DispatchResult,
    DownloadBindingDetail,
    DownloadBindingListData,
)
from ...schemas.common import TypedApiResponse
from ...services.dispatch import DispatchService
from ...services.downloads_workspace import DownloadsWorkspaceService

router = APIRouter(prefix="/downloads", tags=["Downloads"])


@router.get(
    "/bindings",
    summary="List download bindings",
    response_model=TypedApiResponse[DownloadBindingListData],
)
async def list_download_bindings(
    request: Request,
    job_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: DownloadsWorkspaceService = Depends(get_downloads_workspace_service),
) -> TypedApiResponse[DownloadBindingListData]:
    result = service.list_bindings(job_id=job_id, status=status)
    return success_response(
        request,
        data=result,
        message="Download bindings loaded.",
        code="DOWNLOAD_BINDINGS_OK",
        mock=result.mock,
        note="当前 download bindings 列表支持按 job 和 dispatch status 过滤。",
    )


@router.get(
    "/bindings/{binding_id}",
    summary="Get download binding detail",
    response_model=TypedApiResponse[DownloadBindingDetail],
)
async def get_download_binding(
    binding_id: str,
    request: Request,
    service: DownloadsWorkspaceService = Depends(get_downloads_workspace_service),
) -> TypedApiResponse[DownloadBindingDetail]:
    result = service.get_binding(binding_id)
    return success_response(
        request,
        data=result,
        message="Download binding detail loaded.",
        code="DOWNLOAD_BINDING_DETAIL_OK",
        mock=result.mock,
        note="当前 binding detail 会暴露候选、downloader、path handoff 与宿主响应摘要。",
    )


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
