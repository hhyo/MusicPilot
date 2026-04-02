"""Search and metadata route placeholders."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_mvp_placeholder_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.mvp import SearchRequest
from ...services.mvp_placeholder import MvpPlaceholderService

router = APIRouter(tags=["Search", "Metadata"])


@router.post("/search", summary="Search placeholder")
async def search(
    payload: SearchRequest,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.search(payload),
        message="Search placeholder accepted the payload.",
        code="SEARCH_PLACEHOLDER",
        mock=True,
        note="当前搜索结果是契约级 mock 数据，不来自真实元数据源。",
        todo=["Integrate a real metadata source in Phase 2 without changing this response envelope."],
    )


@router.get("/artists/{artist_id}", summary="Artist detail placeholder")
async def artist_detail(
    artist_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.artist_detail(artist_id),
        message="Artist detail placeholder is callable.",
        code="ARTIST_DETAIL_PLACEHOLDER",
        mock=True,
        note="当前艺人详情是 mock 数据，待后续接入真实元数据服务。",
    )


@router.get("/albums/{album_id}", summary="Album detail placeholder")
async def album_detail(
    album_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.album_detail(album_id),
        message="Album detail placeholder is callable.",
        code="ALBUM_DETAIL_PLACEHOLDER",
        mock=True,
        note="当前专辑详情是 mock 数据，待后续接入真实元数据服务。",
    )


@router.get("/tracks/{track_id}", summary="Track detail placeholder")
async def track_detail(
    track_id: str,
    request: Request,
    service: MvpPlaceholderService = Depends(get_mvp_placeholder_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.track_detail(track_id),
        message="Track detail placeholder is callable.",
        code="TRACK_DETAIL_PLACEHOLDER",
        mock=True,
        note="当前歌曲详情是 mock 数据，待后续接入真实元数据服务。",
    )

