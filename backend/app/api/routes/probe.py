"""Host probe route skeletons for Phase 1."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_host_capabilities_service
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...schemas.probe import (
    ProbeConfigRequest,
    ProbeDispatchRequest,
    ProbeNotifyRequest,
    ProbeSearchRequest,
)
from ...services.host_capabilities import HostCapabilitiesService

router = APIRouter(tags=["Probe"])

PROBE_NOTE = "当前返回的是 mock / placeholder 骨架，待后续通过 HostProbeAdapter 接入真实宿主能力。"
PROBE_TODO = [
    "确认宿主真实接口路径、参数和返回结构。",
    "用真实宿主返回样例替换当前 mock 数据。",
]


@router.get("/health", summary="Probe host health capability")
async def probe_health(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.probe_health(),
        message="Probe health placeholder is callable.",
        code="PROBE_HEALTH_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/sites", summary="Probe host sites capability")
async def probe_sites(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_sites(),
        message="Probe sites placeholder is callable.",
        code="PROBE_SITES_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/search", summary="Probe host search capability summary")
async def probe_search_summary(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.search_summary(),
        message="Probe search summary placeholder is callable.",
        code="PROBE_SEARCH_SUMMARY_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/search", summary="Probe host search capability")
async def probe_search(
    payload: ProbeSearchRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.probe_search(payload),
        message="Probe search placeholder accepted the payload.",
        code="PROBE_SEARCH_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/downloaders", summary="Probe host downloader capability")
async def probe_downloaders(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.list_downloaders(),
        message="Probe downloaders placeholder is callable.",
        code="PROBE_DOWNLOADERS_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/dispatch", summary="Probe host dispatch capability")
async def probe_dispatch(
    payload: ProbeDispatchRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.probe_dispatch(payload),
        message="Probe dispatch placeholder accepted the payload.",
        code="PROBE_DISPATCH_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/notify", summary="Probe host notify capability")
async def probe_notify(
    payload: ProbeNotifyRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.probe_notify(payload),
        message="Probe notify placeholder accepted the payload.",
        code="PROBE_NOTIFY_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/config", summary="Probe host config capability summary")
async def probe_config_summary(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.config_summary(),
        message="Probe config summary placeholder is callable.",
        code="PROBE_CONFIG_SUMMARY_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/config", summary="Probe host config capability")
async def probe_config(
    payload: ProbeConfigRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    return success_response(
        request,
        data=service.probe_config(payload),
        message="Probe config placeholder accepted the payload.",
        code="PROBE_CONFIG_PLACEHOLDER",
        mock=True,
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )

