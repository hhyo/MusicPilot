"""Search job routes for the Phase 5 host-aware acquisition loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_query_builder_service, get_search_job_service
from ...core.responses import success_response
from ...schemas.acquisition import QueryBuildRequest, SearchJobCreateRequest
from ...schemas.common import ApiResponse
from ...services.query_builder import QueryBuilderService
from ...services.search_job import SearchJobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/query-preview", summary="Preview query builder output")
async def preview_query(
    payload: QueryBuildRequest,
    request: Request,
    service: QueryBuilderService = Depends(get_query_builder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.build(payload),
        message="QueryBuilder generated a stable PT query payload.",
        code="QUERY_BUILD_OK",
        mock=True,
        note="当前 QueryBuilder 只生成结构化查询词，不会触发真实 PT 搜索。",
    )


@router.get("", summary="List search jobs")
async def list_jobs(
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    jobs = service.list_jobs()
    return success_response(
        request,
        data=jobs,
        message="Search jobs loaded.",
        code="SEARCH_JOBS_OK",
        mock=all(job.mock for job in jobs),
        note="当前任务列表会显示每个 job 最后一次执行所选中的 search adapter。",
    )


@router.post("", summary="Create search job")
async def create_job(
    payload: SearchJobCreateRequest,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    job = service.create_job(payload)
    return success_response(
        request,
        data=job,
        message="Search job created.",
        code="SEARCH_JOB_CREATED",
        mock=job.mock,
        note="创建阶段只生成 metadata 快照与 QueryBuilder 输出；真正的 host/mock adapter 选择在执行阶段完成。",
    )


@router.get("/{job_id}", summary="Get search job detail")
async def get_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    job = service.get_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job detail loaded.",
        code="SEARCH_JOB_DETAIL_OK",
        mock=job.mock,
        note="当前 job detail 会暴露 active search adapter、capability source 与 fallback 信息。",
    )


@router.post("/{job_id}/run", summary="Execute search job synchronously")
async def run_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    job = service.execute_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job executed through the host-aware search resolver.",
        code="SEARCH_JOB_EXECUTED",
        mock=job.mock,
        note="当前执行链路会按 strategy 与 capability 在 host-backed skeleton 和 mock adapter 之间选择，并在需要时回退。",
    )


@router.get("/{job_id}/results", summary="List job candidates")
async def job_results(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    results = service.list_candidates(job_id)
    return success_response(
        request,
        data=results,
        message="Job candidates loaded.",
        code="SEARCH_CANDIDATES_OK",
        mock=results.mock,
        note="当前候选结果会显示 search adapter mode、verification state 与 fallback reason。",
    )
