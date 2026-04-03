"""Organize boundary routes for Phase 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_organize_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.orchestration import OrganizePreviewRequest
from ...services.organize import OrganizeService

router = APIRouter(prefix="/organize", tags=["Organize"])


@router.get("/jobs", summary="List organize previews and records")
async def organize_jobs(
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_records(),
        message="Organize records loaded.",
        code="ORGANIZE_RECORDS_OK",
        mock=True,
        note="当前整理记录来自 mock organize boundary，仅保留状态与后续接入点说明。",
    )


@router.post("/preview", summary="Create organize preview from candidate or binding")
async def preview_organize(
    payload: OrganizePreviewRequest,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.preview(payload),
        message="Organize preview created.",
        code="ORGANIZE_PREVIEW_OK",
        mock=True,
        note="当前只生成 organize preview，不会执行真实文件移动、硬链接、标签写入或媒体库刷新。",
    )
