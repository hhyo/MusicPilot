"""Dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...core.dependencies import get_music_dashboard_chain
from ...core.responses import success_response
from ...schemas.common import ApiResponse
from ...chain.dashboard import MusicDashboardChain

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="Get dashboard summary")
async def dashboard_summary(
    request: Request,
    chain: MusicDashboardChain = Depends(get_music_dashboard_chain),
) -> ApiResponse:
    return success_response(
        request,
        data=chain.summary(),
        message="Dashboard summary loaded.",
        code="DASHBOARD_SUMMARY_OK",
        mock=False,
        note="当前 dashboard 摘要只聚合现有 provider、discovery、handoff、organize 与 scheduler 状态，不伪造探测成功。",
    )
