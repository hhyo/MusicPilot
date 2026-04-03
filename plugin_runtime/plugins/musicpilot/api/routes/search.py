"""Metadata search and detail routes for the Phase 2 minimum loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_metadata_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.metadata import MetadataSearchRequest
from ...services.metadata import MetadataService

router = APIRouter(tags=["Search", "Metadata"])


@router.post("/search", summary="Metadata search (contract-compatible alias)")
@router.post("/metadata/search", summary="Metadata search")
async def search(
    payload: MetadataSearchRequest,
    request: Request,
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.search(payload),
        message="Metadata search completed against the local seed catalog.",
        code="METADATA_SEARCH_OK",
        mock=True,
        note="当前搜索结果来自 local seed metadata，用于打通 Phase 2 最小闭环，不代表已接入真实第三方音乐源。",
        todo=[
            "Replace MockMetadataProviderAdapter with a verified metadata provider in a later phase.",
            "Do not attach PT search, downloader dispatch, or organize logic in this phase.",
        ],
    )


@router.get("/artists/{artist_id}", summary="Artist detail (contract-compatible alias)")
@router.get("/metadata/artists/{artist_id}", summary="Artist detail")
async def artist_detail(
    artist_id: str,
    request: Request,
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_artist_detail(artist_id),
        message="Artist detail loaded from the local seed catalog.",
        code="ARTIST_DETAIL_OK",
        mock=True,
        note="当前艺人详情来自 local seed metadata，待后续接入真实 metadata provider。",
    )


@router.get("/albums/{album_id}", summary="Album detail (contract-compatible alias)")
@router.get("/metadata/albums/{album_id}", summary="Album detail")
async def album_detail(
    album_id: str,
    request: Request,
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_album_detail(album_id),
        message="Album detail loaded from the local seed catalog.",
        code="ALBUM_DETAIL_OK",
        mock=True,
        note="当前专辑详情来自 local seed metadata，待后续接入真实 metadata provider。",
    )


@router.get("/tracks/{track_id}", summary="Track detail (contract-compatible alias)")
@router.get("/metadata/tracks/{track_id}", summary="Track detail")
async def track_detail(
    track_id: str,
    request: Request,
    service: MetadataService = Depends(get_metadata_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.get_track_detail(track_id),
        message="Track detail loaded from the local seed catalog.",
        code="TRACK_DETAIL_OK",
        mock=True,
        note="当前歌曲详情来自 local seed metadata，待后续接入真实 metadata provider。",
    )
