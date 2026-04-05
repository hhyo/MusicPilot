"""Runtime cache helpers that prefer MoviePilot plugin cache and fall back locally."""

from __future__ import annotations

import json
from hashlib import sha1
from typing import Any

from cachetools import TTLCache as LocalTTLCache

try:
    from app.core.cache import TTLCache as HostTTLCache
except Exception:  # pragma: no cover - only exercised outside host plugin runtime
    HostTTLCache = None


class RuntimeTTLCache:
    def __init__(self, *, region: str, maxsize: int, ttl: int) -> None:
        self.region = region
        self._uses_host_cache = HostTTLCache is not None
        if self._uses_host_cache:
            self._cache = HostTTLCache(region=region, maxsize=maxsize, ttl=ttl)
        else:
            self._cache = LocalTTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str, default: Any = None) -> Any:
        if self._uses_host_cache:
            value = self._cache.get(key)
            return default if value is None else value
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if self._uses_host_cache:
            self._cache.set(key, value)
            return
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()


def stable_cache_key(prefix: str, **payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return f"{prefix}:{sha1(encoded.encode('utf-8')).hexdigest()}"
