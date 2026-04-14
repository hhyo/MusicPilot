"""Dispatch routes for the host-aware dispatch boundary."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_music_download_chain
from ...core.responses import success_response
from ...chain.download import MusicDownloadChain
from ...schemas.acquisition import (
    BindingRetryDispatchRequest,
    BindingRetryHandoffResult,
    DispatchRequest,
    DispatchResult,
    DownloadBindingDetail,
    DownloadBindingListData,
    DownloadTaskDetail,
    DownloadTaskListData,
)
from ...schemas.common import TypedApiResponse

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
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[DownloadBindingListData]:
    result = chain.list_bindings(job_id=job_id, status=status)
    return success_response(
        request,
        data=result,
        message="Download bindings loaded.",
        code="DOWNLOAD_BINDINGS_OK",
        mock=result.mock,
        note="当前 download bindings 列表支持按 job 和 dispatch status 过滤。",
    )


@router.get(
    "/tasks",
    summary="List grouped download tasks",
    response_model=TypedApiResponse[DownloadTaskListData],
)
async def list_download_tasks(
    request: Request,
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[DownloadTaskListData]:
    result = chain.list_tasks()
    return success_response(
        request,
        data=result,
        message="Download tasks loaded.",
        code="DOWNLOAD_TASKS_OK",
        mock=result.mock,
        note="当前 download tasks 按 downloader task 聚合 bindings，便于查看 handoff 与重试。",
    )


@router.get(
    "/tasks/{task_id}",
    summary="Get grouped download task detail",
    response_model=TypedApiResponse[DownloadTaskDetail],
)
async def get_download_task(
    task_id: str,
    request: Request,
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[DownloadTaskDetail]:
    result = chain.get_task(task_id)
    return success_response(
        request,
        data=result,
        message="Download task detail loaded.",
        code="DOWNLOAD_TASK_DETAIL_OK",
        mock=result.mock,
    )


@router.get(
    "/bindings/{binding_id}",
    summary="Get download binding detail",
    response_model=TypedApiResponse[DownloadBindingDetail],
)
async def get_download_binding(
    binding_id: str,
    request: Request,
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[DownloadBindingDetail]:
    result = chain.get_binding(binding_id)
    return success_response(
        request,
        data=result,
        message="Download binding detail loaded.",
        code="DOWNLOAD_BINDING_DETAIL_OK",
        mock=result.mock,
        note="当前 binding detail 会暴露候选、downloader、path handoff 与宿主响应摘要。",
    )


@router.post(
    "/bindings/{binding_id}/retry-dispatch",
    summary="Retry a binding dispatch from the original candidate",
    response_model=TypedApiResponse[DownloadBindingDetail],
)
async def retry_dispatch_binding(
    binding_id: str,
    payload: BindingRetryDispatchRequest,
    request: Request,
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[DownloadBindingDetail]:
    result = chain.retry_dispatch(
        binding_id,
        downloader_id=payload.downloader_id,
        manual_confirm=payload.manual_confirm,
    )
    return success_response(
        request,
        data=result,
        message="Binding re-dispatched.",
        code="DOWNLOAD_BINDING_REDISPATCHED",
        mock=result.mock,
    )


@router.post(
    "/bindings/{binding_id}/retry-handoff",
    summary="Retry path handoff resolution for a binding",
    response_model=TypedApiResponse[BindingRetryHandoffResult],
)
async def retry_binding_handoff(
    binding_id: str,
    request: Request,
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[BindingRetryHandoffResult]:
    result = chain.retry_handoff(binding_id)
    return success_response(
        request,
        data=result,
        message="Binding handoff refreshed.",
        code="DOWNLOAD_BINDING_HANDOFF_REFRESHED",
        mock=result.binding.mock,
    )


@router.post(
    "/dispatch",
    summary="Dispatch a candidate to the downloader boundary",
    response_model=TypedApiResponse[DispatchResult],
)
async def dispatch_download(
    payload: DispatchRequest,
    request: Request,
    chain: MusicDownloadChain = Depends(get_music_download_chain),
) -> TypedApiResponse[DispatchResult]:
    result = chain.dispatch(payload)
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
