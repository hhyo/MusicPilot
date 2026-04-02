"""Jobs route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import CreateJobRequest
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", summary="List jobs placeholder")
async def list_jobs(
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_jobs(),
        message="Jobs placeholder is callable.",
        code="JOBS_PLACEHOLDER",
        mock=True,
        note="当前任务列表是 mock 数据，未连接真实获取链路。",
    )


@router.post("", summary="Create job placeholder")
async def create_job(
    payload: CreateJobRequest,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.create_job(payload),
        message="Create job placeholder accepted the payload.",
        code="CREATE_JOB_PLACEHOLDER",
        mock=True,
        note="当前仅验证任务创建契约，不会触发真实 PT 搜索。",
    )


@router.get("/{job_id}/results", summary="List job results placeholder")
async def job_results(
    job_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.job_results(job_id),
        message="Job results placeholder is callable.",
        code="JOB_RESULTS_PLACEHOLDER",
        mock=True,
        note="当前候选结果为 mock 数据，未调用真实 PT 搜索底座。",
    )

