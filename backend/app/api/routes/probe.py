"""Host probe routes with host-aware capability summaries."""

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

PROBE_NOTE = "当前探针会根据配置选择 mock probe 或 host-backed probe，并明确展示 capability source 与 fallback 信息。"
PROBE_TODO = [
    "在真实 MoviePilot 宿主联调后补 verified 结论与样例响应。",
    "继续收敛 host endpoints 的最终字段映射。",
]


def _is_mock(payload: dict) -> bool:
    summary = payload.get("summary", {})
    return summary.get("adapter_mode") == "mock"


@router.get("/health", summary="Probe host health capability")
async def probe_health(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    payload = service.probe_health()
    return success_response(
        request,
        data=payload,
        message="Probe health is callable.",
        code="PROBE_HEALTH_OK",
        mock=_is_mock(payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/sites", summary="Probe host sites capability")
async def probe_sites(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    payload = service.list_sites()
    return success_response(
        request,
        data=payload,
        message="Probe sites is callable.",
        code="PROBE_SITES_OK",
        mock=_is_mock(payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/search", summary="Probe host search capability summary")
async def probe_search_summary(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    payload = service.search_summary()
    return success_response(
        request,
        data=payload,
        message="Probe search summary is callable.",
        code="PROBE_SEARCH_SUMMARY_OK",
        mock=_is_mock(payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/search", summary="Probe host search capability")
async def probe_search(
    payload: ProbeSearchRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    response_payload = service.probe_search(payload)
    return success_response(
        request,
        data=response_payload,
        message="Probe search accepted the payload.",
        code="PROBE_SEARCH_OK",
        mock=_is_mock(response_payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/downloaders", summary="Probe host downloader capability")
async def probe_downloaders(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    payload = service.list_downloaders()
    return success_response(
        request,
        data=payload,
        message="Probe downloaders is callable.",
        code="PROBE_DOWNLOADERS_OK",
        mock=_is_mock(payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/dispatch", summary="Probe host dispatch capability")
async def probe_dispatch(
    payload: ProbeDispatchRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    response_payload = service.probe_dispatch(payload)
    return success_response(
        request,
        data=response_payload,
        message="Probe dispatch accepted the payload.",
        code="PROBE_DISPATCH_OK",
        mock=_is_mock(response_payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/notify", summary="Probe host notify capability")
async def probe_notify(
    payload: ProbeNotifyRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    response_payload = service.probe_notify(payload)
    return success_response(
        request,
        data=response_payload,
        message="Probe notify accepted the payload.",
        code="PROBE_NOTIFY_OK",
        mock=_is_mock(response_payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.get("/config", summary="Probe host config capability summary")
async def probe_config_summary(
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    payload = service.config_summary()
    return success_response(
        request,
        data=payload,
        message="Probe config summary is callable.",
        code="PROBE_CONFIG_SUMMARY_OK",
        mock=_is_mock(payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )


@router.post("/config", summary="Probe host config capability")
async def probe_config(
    payload: ProbeConfigRequest,
    request: Request,
    service: HostCapabilitiesService = Depends(get_host_capabilities_service),
) -> ApiResponse:
    response_payload = service.probe_config(payload)
    return success_response(
        request,
        data=response_payload,
        message="Probe config accepted the payload.",
        code="PROBE_CONFIG_OK",
        mock=_is_mock(response_payload),
        note=PROBE_NOTE,
        todo=PROBE_TODO,
    )
