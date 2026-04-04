"""Organize boundary routes for the transfer-aware preview/apply flow."""

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
        note="当前 organize records 会展示 organize backend、status、verification state、handoff source 与 fallback 信息。",
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
        note="当前 organize preview 已收口为本地音乐路径预览：基于明确的 source_path 和音乐 metadata snapshot 生成本地 plan preview，不再依赖宿主影视预览语义。",
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
        note="当前 organize apply 会在 mock apply 与真实宿主底层文件/存储执行之间二选一。缺少 organize input 时会直接失败，不会再自动切换到其他业务路径。",
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
        note="当前 organize record detail 会显示 preview/apply 状态流、backend、path handoff 与失败原因。",
    )
