"""Unified music media resolve routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_music_media_chain
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.music_media import MusicPrepareRequest, MusicResolveDetailRequest, MusicResolveRequest

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/prepare", summary="Prepare music media recognition input")
async def prepare_media(
    payload: MusicPrepareRequest,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    prepared = chain.prepare(payload.input)
    return success_response(
        request,
        data=prepared,
        message="Music media prepared.",
        code="MUSIC_MEDIA_PREPARE_OK",
        mock=False,
    )


@router.post("/resolve", summary="Resolve music media")
async def resolve_media(
    payload: MusicResolveRequest,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    media = chain.resolve_response(payload.input)
    return success_response(
        request,
        data=media,
        message="Music media resolved.",
        code="MUSIC_MEDIA_RESOLVE_OK",
        mock=False,
    )


@router.post("/resolve/detail", summary="Resolve music media detail")
async def resolve_media_detail(
    payload: MusicResolveDetailRequest,
    request: Request,
    chain=Depends(get_music_media_chain),
) -> ApiResponse:
    result = chain.resolve_detail(payload.input)
    return success_response(
        request,
        data=result,
        message="Music media detail resolved.",
        code="MUSIC_MEDIA_DETAIL_OK",
        mock=False,
    )
