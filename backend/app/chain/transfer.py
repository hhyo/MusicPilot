"""Transfer chain skeleton."""

from __future__ import annotations

from app.chain import MusicChainBase


class MusicTransferChain(MusicChainBase):
    def __init__(self, **deps) -> None:
        super().__init__(cache_region="music_transfer_chain")
        self.deps = deps

