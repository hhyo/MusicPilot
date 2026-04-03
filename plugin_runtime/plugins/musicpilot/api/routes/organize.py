"""Organize boundary routes for the Phase 9 transfer-aware preview/apply flow."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_organize_service
from ...core.responses import success_response
from ...schemas.common import TypedApiResponse
from ...schemas.orchestration import (
    OrganizeApplyRequest,
    OrganizePreviewRequest,
    OrganizePreviewResult,
    OrganizeRecordListData,
)
from ...services.organize import OrganizeService

router = APIRouter(prefix="/organize", tags=["Organize"])


@router.get(
    "/jobs",
    summary="List organize records",
    response_model=TypedApiResponse[OrganizeRecordListData],
)
async def organize_jobs(
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizeRecordListData]:
    records = service.list_records()
    return success_response(
        request,
        data=records,
        message="Organize records loaded.",
        code="ORGANIZE_RECORDS_OK",
        mock=records.mock,
        note="当前 organize records 会展示 organize backend、status、verification state、matrix status 与 fallback 信息。",
    )


@router.post(
    "/preview",
    summary="Create organize preview from candidate or binding",
    response_model=TypedApiResponse[OrganizePreviewResult],
)
async def preview_organize(
    payload: OrganizePreviewRequest,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizePreviewResult]:
    result = service.preview(payload)
    return success_response(
        request,
        data=result,
        message="Organize preview created.",
        code="ORGANIZE_PREVIEW_OK",
        mock=result.mock,
        note="当前 organize preview 会按 strategy 和 capability 在真实 MoviePilot transfer/name 映射与 mock organize 之间选择，并尽量优先显示更稳的 transfer-history handoff 来源。",
    )


@router.post(
    "/apply",
    summary="Apply an organize preview/record",
    response_model=TypedApiResponse[OrganizePreviewResult],
)
async def apply_organize(
    payload: OrganizeApplyRequest,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizePreviewResult]:
    result = service.apply(payload)
    return success_response(
        request,
        data=result,
        message="Organize apply handled the record.",
        code="ORGANIZE_APPLY_OK",
        mock=result.mock,
        note="当前 organize apply 可能是 mock apply，也可能映射到真实 MoviePilot transfer/manual；Phase 9 对已知 blocked 组合会在真正发送 host apply 前显式阻断，并返回 strategy decision。",
    )


@router.get(
    "/jobs/{record_id}",
    summary="Get organize record detail",
    response_model=TypedApiResponse[OrganizePreviewResult],
)
async def organize_job_detail(
    record_id: str,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizePreviewResult]:
    result = service.get_record(record_id)
    return success_response(
        request,
        data=result,
        message="Organize record detail loaded.",
        code="ORGANIZE_RECORD_DETAIL_OK",
        mock=result.mock,
        note="当前 organize record detail 会显示 preview/apply 状态流、backend、path handoff、matrix status 与失败原因。",
    )
