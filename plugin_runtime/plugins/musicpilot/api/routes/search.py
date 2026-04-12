"""Metadata search and direct detail routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_metadata_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.metadata import MetadataSearchRequest
from ...services.metadata import MetadataService

router = APIRouter(tags=["Search", "Metadata"])


def _is_mock_source(source_type: str) -> bool:
    return source_type in {"mock", "local_seed"}


@router.post("/search", summary="Metadata search")
@router.post("/metadata/search", summary="Metadata search")
async def search(
    payload: MetadataSearchRequest,
    request: Request,
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    result = service.search(payload)
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
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    detail = service.get_artist_detail(artist_id)
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
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    detail = service.get_album_detail(album_id)
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
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    detail = service.get_track_detail(track_id)
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
