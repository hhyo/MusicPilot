"""MusicPilot runtime-capable package.

用途：
- 作为本地 FastAPI 工程的包根
- 作为 plugin_runtime 装配后的插件包根
- 保留最小版本号和插件元信息

注意：
- 当前阶段不实现真实 MoviePilot 插件注册逻辑
- 当前阶段不声明不存在的宿主 API
- 后续仅在宿主契约明确后补真实入口与注册信息
"""

from __future__ import annotations

from typing import Any

try:
    from app.plugins import _PluginBase as _HostPluginBase
except Exception:  # pragma: no cover - only available inside MoviePilot host runtime
    _HostPluginBase = None

__version__ = "0.1.0"
PLUGIN_NAME = "MusicPilot"
PLUGIN_DESCRIPTION = "Phase 6 runtime placeholder with host-aware search/dispatch/organize wiring for future MoviePilot integration."


def _bootstrap_plugin_storage() -> None:
    from .services.metadata import bootstrap_metadata_storage

    bootstrap_metadata_storage()


def _build_plugin_api_manifest() -> list[dict[str, Any]]:
    from .api.router import plugin_api_router

    apis: list[dict[str, Any]] = []
    for route in plugin_api_router.routes:
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        methods = sorted(
            method for method in (getattr(route, "methods", None) or set())
            if method not in {"HEAD", "OPTIONS"}
        )
        if not path or not endpoint or not methods:
            continue
        apis.append(
            {
                "path": path,
                "endpoint": endpoint,
                "methods": methods,
                "summary": getattr(route, "summary", None) or getattr(route, "name", path),
                "description": getattr(route, "description", None) or "",
            }
        )
    return apis


if _HostPluginBase is not None:
    class musicpilot(_HostPluginBase):
        """Minimal MoviePilot plugin entry for loading MusicPilot runtime in-process."""

        plugin_name = PLUGIN_NAME
        plugin_desc = PLUGIN_DESCRIPTION
        plugin_version = __version__
        plugin_order = 999

        def __init__(self):
            super().__init__()
            self._config: dict[str, Any] = {}
            self._enabled = True
            self._storage_bootstrapped = False

        def init_plugin(self, config: dict = None):
            self._config = config or {}
            self._enabled = bool(self._config.get("enabled", True))
            if self._enabled and not self._storage_bootstrapped:
                _bootstrap_plugin_storage()
                self._storage_bootstrapped = True

        def get_state(self) -> bool:
            return self._enabled

        def get_api(self) -> list[dict[str, Any]]:
            if not self._enabled:
                return []
            return _build_plugin_api_manifest()

        def get_form(self):
            return [], {"enabled": True}

        def get_page(self):
            return []

        def stop_service(self):
            return None
