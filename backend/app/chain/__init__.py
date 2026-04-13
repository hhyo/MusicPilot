"""MoviePilot-aligned chain base for MusicPilot."""

from __future__ import annotations

from app import logger
from app.core.runtime_cache import RuntimeTTLCache


class MusicChainBase:
    """Shared base for all top-level MusicPilot chains."""

    def __init__(self, *, cache_region: str = "music_chain", cache_ttl: int = 300, cache_maxsize: int = 256) -> None:
        self.logger = logger
        self.cache = RuntimeTTLCache(region=cache_region, ttl=cache_ttl, maxsize=cache_maxsize)
