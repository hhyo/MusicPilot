"""Dispatch routes for the Phase 5 host-aware dispatch boundary."""

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
    result = service.dispatch(payload)
    return success_response(
        request,
        data=result,
        message="Dispatch boundary handled the candidate.",
        code="DISPATCH_BOUNDARY_OK",
        mock=result.dispatch_backend == "mock",
        note="当前 dispatch 会优先尝试 host-backed adapter skeleton；若能力缺失、配置不完整或运行失败，会按策略回退到 mock。",
        todo=["Replace the host dispatch skeleton with a verified MoviePilot downloader integration after joint validation."],
    )
