"""Dispatch routes for the Phase 3 minimum acquisition loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_dispatch_service
from ...core.responses import success_response
from ...schemas.acquisition import DispatchRequest
from ...schemas.common import ApiResponse
from ...services.dispatch import DispatchService

router = APIRouter(prefix="/downloads", tags=["Downloads"])


@router.post("/dispatch", summary="Dispatch a candidate to the downloader boundary")
async def dispatch_download(
    payload: DispatchRequest,
    request: Request,
    service: DispatchService = Depends(get_dispatch_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.dispatch(payload),
        message="Dispatch boundary handled the candidate.",
        code="DISPATCH_BOUNDARY_OK",
        mock=True,
        note="当前为 mock dispatch，已保留真实下载器接入边界，但不会真正下发到宿主下载器。",
        todo=["Replace MockDownloadDispatchAdapter with a verified downloader integration in a later phase."],
    )
