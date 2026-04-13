"""Media chain skeleton."""

from __future__ import annotations

from app.chain import MusicChainBase


class MusicMediaChain(MusicChainBase):
    def __init__(self, **deps) -> None:
        super().__init__(cache_region="music_media_chain")
        self.deps = deps

