"""Organize boundary routes for Phase 6 host-aware preview/apply flow."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_organize_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.orchestration import OrganizeApplyRequest, OrganizePreviewRequest
from ...services.organize import OrganizeService

router = APIRouter(prefix="/organize", tags=["Organize"])


@router.get("/jobs", summary="List organize records")
async def organize_jobs(
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> ApiResponse:
    records = service.list_records()
    return success_response(
        request,
        data=records,
        message="Organize records loaded.",
        code="ORGANIZE_RECORDS_OK",
        mock=records.mock,
        note="当前 organize records 会展示 organize backend、status、verification state 与 fallback 信息。",
    )


@router.post("/preview", summary="Create organize preview from candidate or binding")
async def preview_organize(
    payload: OrganizePreviewRequest,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> ApiResponse:
    result = service.preview(payload)
    return success_response(
        request,
        data=result,
        message="Organize preview created.",
        code="ORGANIZE_PREVIEW_OK",
        mock=result.mock,
        note="当前 organize preview 会按 strategy 和 capability 在 host-backed skeleton 与 mock organize 之间选择。",
    )


@router.post("/apply", summary="Apply an organize preview/record")
async def apply_organize(
    payload: OrganizeApplyRequest,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> ApiResponse:
    result = service.apply(payload)
    return success_response(
        request,
        data=result,
        message="Organize apply handled the record.",
        code="ORGANIZE_APPLY_OK",
        mock=result.mock,
        note="当前 organize apply 可能是 mock apply，也可能是 host-backed skeleton；结果会明确显示 backend、fallback 与 verification state。",
    )


@router.get("/jobs/{record_id}", summary="Get organize record detail")
async def organize_job_detail(
    record_id: str,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> ApiResponse:
    result = service.get_record(record_id)
    return success_response(
        request,
        data=result,
        message="Organize record detail loaded.",
        code="ORGANIZE_RECORD_DETAIL_OK",
        mock=result.mock,
        note="当前 organize record detail 会显示 preview/apply 状态流、backend 与失败原因。",
    )
