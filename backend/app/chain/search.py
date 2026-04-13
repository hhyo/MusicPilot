"""Search chain skeleton."""

from __future__ import annotations

from app.chain import MusicChainBase


class MusicSearchChain(MusicChainBase):
    def __init__(self, **deps) -> None:
        super().__init__(cache_region="music_search_chain")
        self.deps = deps

