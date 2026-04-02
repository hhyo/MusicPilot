"""Downloads route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import DispatchDownloadRequest
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(prefix="/downloads", tags=["Downloads"])


@router.post("/dispatch", summary="Dispatch download placeholder")
async def dispatch_download(
    payload: DispatchDownloadRequest,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.dispatch_download(payload),
        message="Dispatch placeholder accepted the payload.",
        code="DISPATCH_PLACEHOLDER",
        mock=True,
        note="当前仅验证下载派发契约，不会调用真实下载器。",
        todo=["Replace dry-run binding with real downloader dispatch in later phases."],
    )

