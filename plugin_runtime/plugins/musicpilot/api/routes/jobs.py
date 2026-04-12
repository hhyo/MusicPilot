"""Search job routes for the host-aware acquisition loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_query_builder_service, get_search_job_service
from ...core.responses import success_response
from ...schemas.acquisition import (
    QueryBuildRequest,
    QueryBuildResult,
    SearchCandidateListData,
    SearchJobCreateRequest,
    SearchJobSummary,
    MutationResult,
)
from ...schemas.common import TypedApiResponse
from ...services.query_builder import QueryBuilderService
from ...services.search_job import SearchJobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "/query-preview",
    summary="Preview query builder output",
    response_model=TypedApiResponse[QueryBuildResult],
)
async def preview_query(
    payload: QueryBuildRequest,
    request: Request,
    service: QueryBuilderService = Depends(get_query_builder_service),
) -> TypedApiResponse[QueryBuildResult]:
    return success_response(
        request,
        data=service.build(payload),
        message="QueryBuilder generated a stable PT query payload.",
        code="QUERY_BUILD_OK",
        mock=True,
        note="当前 QueryBuilder 只生成结构化查询词，不会触发真实 PT 搜索。",
    )


@router.get(
    "",
    summary="List search jobs",
    response_model=TypedApiResponse[list[SearchJobSummary]],
)
async def list_jobs(
    request: Request,
    status: str | None = Query(default=None),
    trigger_source: str | None = Query(default=None),
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[list[SearchJobSummary]]:
    jobs = service.list_jobs(status=status, trigger_source=trigger_source)
    return success_response(
        request,
        data=jobs,
        message="Search jobs loaded.",
        code="SEARCH_JOBS_OK",
        mock=all(job.mock for job in jobs),
        note="当前任务列表会显示 search adapter、capability source、fallback 与最近一次真实执行摘要。",
    )


@router.post(
    "",
    summary="Create search job",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def create_job(
    payload: SearchJobCreateRequest,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[SearchJobSummary]:
    job = service.create_job(payload)
    return success_response(
        request,
        data=job,
        message="Search job created.",
        code="SEARCH_JOB_CREATED",
        mock=job.mock,
        note="创建阶段只生成 metadata 快照与 QueryBuilder 输出；真正的 host/mock adapter 选择在执行阶段完成。",
    )


@router.get(
    "/{job_id}",
    summary="Get search job detail",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def get_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[SearchJobSummary]:
    job = service.get_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job detail loaded.",
        code="SEARCH_JOB_DETAIL_OK",
        mock=job.mock,
        note="当前 job detail 会暴露 active search adapter、capability source、fallback 与 search/query 摘要。",
    )


@router.post(
    "/{job_id}/run",
    summary="Execute search job synchronously",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def run_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[SearchJobSummary]:
    job = service.execute_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job executed through the host-aware search resolver.",
        code="SEARCH_JOB_EXECUTED",
        mock=job.mock,
        note="当前执行链路只暴露真实采用的 search 语义与 adapter。",
    )


@router.post(
    "/{job_id}/retry",
    summary="Retry search job synchronously",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def retry_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[SearchJobSummary]:
    job = service.retry_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job retried.",
        code="SEARCH_JOB_RETRIED",
        mock=job.mock,
        note="retry 会重置旧候选并按当前 host-aware search resolver 重新执行。",
    )


@router.delete(
    "/{job_id}",
    summary="Delete search job",
    response_model=TypedApiResponse[MutationResult],
)
async def delete_job(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[MutationResult]:
    result = service.delete_job(job_id)
    return success_response(
        request,
        data=result,
        message="Search job deleted.",
        code="SEARCH_JOB_DELETED",
        mock=False,
    )


@router.get(
    "/{job_id}/results",
    summary="List job candidates",
    response_model=TypedApiResponse[SearchCandidateListData],
)
async def job_results(
    job_id: str,
    request: Request,
    service: SearchJobService = Depends(get_search_job_service),
) -> TypedApiResponse[SearchCandidateListData]:
    results = service.list_candidates(job_id)
    return success_response(
        request,
        data=results,
        message="Job candidates loaded.",
        code="SEARCH_CANDIDATES_OK",
        mock=results.mock,
        note="当前候选结果会显示 search adapter mode、verification state、path handoff 与 fallback reason。",
    )
