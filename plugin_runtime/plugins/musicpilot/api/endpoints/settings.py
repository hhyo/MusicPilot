"""Settings routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...chain.system import MusicSystemChain
from ...core.dependencies import get_music_system_chain
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.shared import ProviderSettingsUpdatePayload, RuleProfile

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/providers", summary="Get provider settings")
async def provider_settings(
    request: Request,
    chain: MusicSystemChain = Depends(get_music_system_chain),
) -> ApiResponse:
    return success_response(
        request,
        data=chain.provider_settings(),
        message="Provider settings loaded.",
        code="SETTINGS_PROVIDERS_OK",
        mock=False,
    )


@router.put("/providers", summary="Update provider settings")
async def update_provider_settings(
    payload: ProviderSettingsUpdatePayload,
    request: Request,
    chain: MusicSystemChain = Depends(get_music_system_chain),
) -> ApiResponse:
    return success_response(
        request,
        data=chain.update_provider_settings(payload),
        message="Provider settings updated.",
        code="UPDATE_SETTINGS_PROVIDERS_OK",
        mock=False,
    )


@router.get("/profiles", summary="Get rule profiles")
async def rule_profiles(
    request: Request,
    chain: MusicSystemChain = Depends(get_music_system_chain),
) -> ApiResponse:
    return success_response(
        request,
        data=chain.rule_profiles(),
        message="Rule profiles loaded.",
        code="SETTINGS_PROFILES_OK",
        mock=False,
    )


@router.put("/profiles", summary="Update rule profile")
async def update_rule_profile(
    payload: RuleProfile,
    request: Request,
    chain: MusicSystemChain = Depends(get_music_system_chain),
) -> ApiResponse:
    return success_response(
        request,
        data=chain.update_rule_profile(payload),
        message="Rule profile updated.",
        code="UPDATE_SETTINGS_PROFILE_OK",
        mock=False,
    )
