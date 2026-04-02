"""Organize route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(tags=["Organize"])


@router.get("/organize/jobs", summary="List organize jobs placeholder")
async def organize_jobs(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.organize_jobs(),
        message="Organize jobs placeholder is callable.",
        code="ORGANIZE_JOBS_PLACEHOLDER",
        mock=True,
        note="当前整理任务为 mock 数据，未进入真实整理或入库流程。",
    )


@router.post("/library/items/{item_id}/retry", summary="Retry organize placeholder")
async def retry_library_item(
    item_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.retry_library_item(item_id),
        message="Retry organize placeholder is callable.",
        code="RETRY_ORGANIZE_PLACEHOLDER",
        mock=True,
        note="当前仅验证整理重试契约，不会操作真实媒体库。",
    )

