"""Search and metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from ...core.dependencies import get_music_media_chain, get_music_search_chain
from ...core.responses import success_response
from ...schemas.acquisition import (
    MutationResult,
    QueryBuildRequest,
    QueryBuildResult,
    SearchCandidateActionResult,
    SearchCandidateConfirmRequest,
    SearchCandidateListData,
    SearchCandidateRejectRequest,
    SearchJobCreateRequest,
    SearchJobSummary,
)
from ...schemas.common import ApiResponse, TypedApiResponse
from ...schemas.metadata import MetadataSearchRequest
from ...schemas.shared import EntityType
from ...chain.search import MusicSearchChain

router = APIRouter(tags=["Search", "Metadata"])
jobs_router = APIRouter(prefix="/jobs", tags=["Search"])


def _is_mock_source(source_type: str) -> bool:
    return source_type in {"mock", "local_seed"}


@router.post("/search", summary="Metadata search")
@router.post("/metadata/search", summary="Metadata search")
async def search(
    payload: MetadataSearchRequest,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    result = chain.search_metadata(payload)
    return success_response(
        request,
        data=result,
        message="Metadata search completed.",
        code="METADATA_SEARCH_OK",
        mock=_is_mock_source(result.source_type),
        note=(
            "当前搜索结果来自 local seed metadata，用于打通最小搜索闭环。"
            if _is_mock_source(result.source_type)
            else "当前搜索结果来自真实 metadata provider。"
        ),
        todo=[
            "Do not attach PT search, downloader dispatch, or organize logic in this phase.",
        ],
    )


@router.get("/artists/{artist_id}", summary="Artist detail")
@router.get("/metadata/artists/{artist_id}", summary="Artist detail")
async def artist_detail(
    artist_id: str,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    detail = chain.resolve_detail_from_active_provider_ref(
        entity_type=EntityType.ARTIST,
        provider_id=artist_id,
        source_kind="detail",
        source_context={"entrypoint": "metadata_detail_route"},
        raw_context={},
    ).detail
    return success_response(
        request,
        data=detail,
        message="Artist detail loaded.",
        code="ARTIST_DETAIL_OK",
        mock=detail.mock,
        note=(
            "当前艺人详情来自 local seed metadata。"
            if detail.mock
            else "当前艺人详情来自真实 metadata provider。"
        ),
    )


@router.get("/albums/{album_id}", summary="Album detail")
@router.get("/metadata/albums/{album_id}", summary="Album detail")
async def album_detail(
    album_id: str,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    detail = chain.resolve_detail_from_active_provider_ref(
        entity_type=EntityType.ALBUM,
        provider_id=album_id,
        source_kind="detail",
        source_context={"entrypoint": "metadata_detail_route"},
        raw_context={},
    ).detail
    return success_response(
        request,
        data=detail,
        message="Album detail loaded.",
        code="ALBUM_DETAIL_OK",
        mock=detail.mock,
        note=(
            "当前专辑详情来自 local seed metadata。"
            if detail.mock
            else "当前专辑详情来自真实 metadata provider。"
        ),
    )


@router.get("/tracks/{track_id}", summary="Track detail")
@router.get("/metadata/tracks/{track_id}", summary="Track detail")
async def track_detail(
    track_id: str,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    detail = chain.resolve_detail_from_active_provider_ref(
        entity_type=EntityType.TRACK,
        provider_id=track_id,
        source_kind="detail",
        source_context={"entrypoint": "metadata_detail_route"},
        raw_context={},
    ).detail
    return success_response(
        request,
        data=detail,
        message="Track detail loaded.",
        code="TRACK_DETAIL_OK",
        mock=detail.mock,
        note=(
            "当前歌曲详情来自 local seed metadata。"
            if detail.mock
            else "当前歌曲详情来自真实 metadata provider。"
        ),
    )


@jobs_router.post(
    "/query-preview",
    summary="Preview query builder output",
    response_model=TypedApiResponse[QueryBuildResult],
)
async def preview_query(
    payload: QueryBuildRequest,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[QueryBuildResult]:
    return success_response(
        request,
        data=chain.build_query(payload),
        message="QueryBuilder generated a stable PT query payload.",
        code="QUERY_BUILD_OK",
        mock=True,
        note="当前 QueryBuilder 只生成结构化查询词，不会触发真实 PT 搜索。",
    )


@jobs_router.get(
    "",
    summary="List search jobs",
    response_model=TypedApiResponse[list[SearchJobSummary]],
)
async def list_jobs(
    request: Request,
    status: str | None = Query(default=None),
    trigger_source: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    has_dispatch: bool | None = Query(default=None),
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[list[SearchJobSummary]]:
    jobs = chain.list_jobs(
        status=status,
        trigger_source=trigger_source,
        decision=decision,
        has_dispatch=has_dispatch,
    )
    return success_response(
        request,
        data=jobs,
        message="Search jobs loaded.",
        code="SEARCH_JOBS_OK",
        mock=all(job.mock for job in jobs),
        note="当前任务列表会显示 search adapter、capability source、fallback 与最近一次真实执行摘要。",
    )


@jobs_router.post(
    "",
    summary="Create search job",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def create_job(
    payload: SearchJobCreateRequest,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchJobSummary]:
    job = chain.create_job(payload)
    return success_response(
        request,
        data=job,
        message="Search job created.",
        code="SEARCH_JOB_CREATED",
        mock=job.mock,
        note="创建阶段只生成 metadata 快照与 QueryBuilder 输出；真正的 host/mock adapter 选择在执行阶段完成。",
    )


@jobs_router.get(
    "/{job_id}",
    summary="Get search job detail",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def get_job(
    job_id: str,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchJobSummary]:
    job = chain.get_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job detail loaded.",
        code="SEARCH_JOB_DETAIL_OK",
        mock=job.mock,
        note="当前 job detail 会暴露 active search adapter、capability source、fallback 与 search/query 摘要。",
    )


@jobs_router.post(
    "/{job_id}/run",
    summary="Execute search job synchronously",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def run_job(
    job_id: str,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchJobSummary]:
    job = chain.execute_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job executed through the host-aware search resolver.",
        code="SEARCH_JOB_EXECUTED",
        mock=job.mock,
        note="当前执行链路只暴露真实采用的 search 语义与 adapter。",
    )


@jobs_router.post(
    "/{job_id}/retry",
    summary="Retry search job synchronously",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def retry_job(
    job_id: str,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchJobSummary]:
    job = chain.retry_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job retried.",
        code="SEARCH_JOB_RETRIED",
        mock=job.mock,
        note="retry 会重置旧候选并按当前 host-aware search resolver 重新执行。",
    )


@jobs_router.post(
    "/{job_id}/cancel",
    summary="Cancel queued or running search job",
    response_model=TypedApiResponse[SearchJobSummary],
)
async def cancel_job(
    job_id: str,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchJobSummary]:
    job = chain.cancel_job(job_id)
    return success_response(
        request,
        data=job,
        message="Search job cancelled.",
        code="SEARCH_JOB_CANCELLED",
        mock=job.mock,
    )


@jobs_router.delete(
    "/{job_id}",
    summary="Delete search job",
    response_model=TypedApiResponse[MutationResult],
)
async def delete_job(
    job_id: str,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[MutationResult]:
    result = chain.delete_job(job_id)
    return success_response(
        request,
        data=result,
        message="Search job deleted.",
        code="SEARCH_JOB_DELETED",
        mock=False,
    )


@jobs_router.post(
    "/{job_id}/candidates/{candidate_id}/confirm",
    summary="Confirm candidate and dispatch it",
    response_model=TypedApiResponse[SearchCandidateActionResult],
)
async def confirm_candidate(
    job_id: str,
    candidate_id: str,
    payload: SearchCandidateConfirmRequest,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchCandidateActionResult]:
    result = chain.confirm_candidate(job_id, candidate_id, payload)
    return success_response(
        request,
        data=result,
        message="Candidate confirmed.",
        code="SEARCH_CANDIDATE_CONFIRMED",
        mock=result.job.mock,
    )


@jobs_router.post(
    "/{job_id}/candidates/{candidate_id}/reject",
    summary="Reject candidate",
    response_model=TypedApiResponse[SearchCandidateActionResult],
)
async def reject_candidate(
    job_id: str,
    candidate_id: str,
    payload: SearchCandidateRejectRequest,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchCandidateActionResult]:
    result = chain.reject_candidate(job_id, candidate_id, payload)
    return success_response(
        request,
        data=result,
        message="Candidate rejected.",
        code="SEARCH_CANDIDATE_REJECTED",
        mock=result.job.mock,
    )


@jobs_router.get(
    "/{job_id}/results",
    summary="List job candidates",
    response_model=TypedApiResponse[SearchCandidateListData],
)
async def job_results(
    job_id: str,
    request: Request,
    chain: MusicSearchChain = Depends(get_music_search_chain),
) -> TypedApiResponse[SearchCandidateListData]:
    results = chain.list_candidates(job_id)
    return success_response(
        request,
        data=results,
        message="Job candidates loaded.",
        code="SEARCH_CANDIDATES_OK",
        mock=results.mock,
        note="当前候选列表会显示评分、decision、dispatch status、verification state 与 path handoff 摘要。",
    )


__all__ = ["jobs_router", "router"]
