"""Dashboard chain skeleton."""

from __future__ import annotations

from app.chain import MusicChainBase


class MusicDashboardChain(MusicChainBase):
    def __init__(self, **deps) -> None:
        super().__init__(cache_region="music_dashboard_chain")
        self.deps = deps

