"""Search job routes for the Phase 3 minimum acquisition loop."""

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
    return success_response(
        request,
        data=service.list_jobs(),
        message="Search jobs loaded.",
        code="SEARCH_JOBS_OK",
        mock=True,
        note="当前任务列表基于 Phase 3 mock acquisition 链路。",
    )


@router.post("", summary="Create search job")
async def create_job(
    payload: SearchJobCreateRequest,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.create_job(payload),
        message="Search job created.",
        code="SEARCH_JOB_CREATED",
        mock=True,
        note="当前只创建 mock SearchJob，并保存 QueryBuilder 结果与 metadata 快照。",
    )


@router.get("/{job_id}", summary="Get search job detail")
async def get_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_job(job_id),
        message="Search job detail loaded.",
        code="SEARCH_JOB_DETAIL_OK",
        mock=True,
        note="当前 job detail 反映的是 Phase 3 mock 执行链路状态。",
    )


@router.post("/{job_id}/run", summary="Execute search job synchronously")
async def run_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.execute_job(job_id),
        message="Search job executed with the mock host search adapter.",
        code="SEARCH_JOB_EXECUTED",
        mock=True,
        note="当前执行链路使用 mock host search adapter 和 mock scorer，不代表真实 PT 搜索。",
    )


@router.get("/{job_id}/results", summary="List job candidates")
async def job_results(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_candidates(job_id),
        message="Job candidates loaded.",
        code="SEARCH_CANDIDATES_OK",
        mock=True,
        note="当前候选结果来自 mock host search adapter，评分与决策仅用于 Phase 3 最小闭环验证。",
    )
