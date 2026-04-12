"""Organize boundary routes for the transfer-aware preview/apply flow."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

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
    status: str | None = Query(default=None),
    organize_backend: str | None = Query(default=None),
    verification_state: str | None = Query(default=None),
    candidate_id: str | None = Query(default=None),
    binding_id: str | None = Query(default=None),
    search_job_id: str | None = Query(default=None),
    subscription_run_id: str | None = Query(default=None),
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizeRecordListData]:
    records = service.list_records(
        status=status,
        organize_backend=organize_backend,
        verification_state=verification_state,
        candidate_id=candidate_id,
        binding_id=binding_id,
        search_job_id=search_job_id,
        subscription_run_id=subscription_run_id,
    )
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
        note="当前 organize preview 已收口为本地音乐路径预览：基于音乐 metadata、现有上下文与 organize 模板生成本地 plan preview，不再依赖宿主影视预览语义。",
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


@router.post(
    "/jobs/{record_id}/retry",
    summary="Retry organize apply from an existing record",
    response_model=TypedApiResponse[OrganizePreviewResult],
)
async def retry_organize_job(
    record_id: str,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizePreviewResult]:
    result = service.retry(record_id)
    return success_response(
        request,
        data=result,
        message="Organize record retried.",
        code="ORGANIZE_RETRY_OK",
        mock=result.mock,
        note="retry 会直接复用既有 organize record 的上下文和 preview 计划重新 apply。",
    )


@router.post(
    "/jobs/{record_id}/rebuild-preview",
    summary="Rebuild organize preview from an existing record",
    response_model=TypedApiResponse[OrganizePreviewResult],
)
async def rebuild_organize_preview(
    record_id: str,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizePreviewResult]:
    result = service.rebuild_preview(record_id)
    return success_response(
        request,
        data=result,
        message="Organize preview rebuilt.",
        code="ORGANIZE_REBUILD_PREVIEW_OK",
        mock=result.mock,
        note="rebuild-preview 会基于当前 record 的 candidate/binding 上下文重建 preview，不会切换到新的业务语义。",
    )


@router.post(
    "/jobs/{record_id}/repair-source-path",
    summary="Repair source path and rebuild organize preview",
    response_model=TypedApiResponse[OrganizePreviewResult],
)
async def repair_organize_source_path(
    record_id: str,
    request: Request,
    service: OrganizeService = Depends(get_organize_service),
) -> TypedApiResponse[OrganizePreviewResult]:
    result = service.repair_source_path(record_id)
    return success_response(
        request,
        data=result,
        message="Organize source path repaired.",
        code="ORGANIZE_REPAIR_SOURCE_PATH_OK",
        mock=result.mock,
        note="repair-source-path 会尝试补回现有 candidate/binding 的 source path 语义，再重建 preview。",
    )
